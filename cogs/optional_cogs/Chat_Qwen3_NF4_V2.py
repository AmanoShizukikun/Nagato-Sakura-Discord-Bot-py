import discord
from discord import app_commands
from discord.ext import commands
import os
import torch
import gc
from threading import Thread
from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

try:
    from opencc import OpenCC
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False
    print("警告: OpenCC 套件未安裝，繁簡轉換功能將被禁用")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("警告: Whisper 套件未安裝，語音轉文字功能將被禁用")

# 預設基礎模型路徑
BASE_MODEL_PATH = os.environ.get("QWEN_BASE_MODEL_PATH", "Qwen/Qwen3-4B-Instruct-2507")
# 如果你想使用本地基礎模型，請將下面這行取消註解並修改路徑
# BASE_MODEL_PATH = r"模型路徑"
BASE_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Chat", "models", "Qwen3-4B-Instruct-2507")

# LoRA 適配器路徑（可選，設為 None 表示不使用 LoRA）
LORA_PATH = None
# 如果你想使用LoRA模型，請將下面這行取消註解並修改路徑
# LORA_PATH = r"模型路徑"
LORA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Chat", "lora", "NS-V1-Qwen3")

def check_model_path(model_path):
    if os.path.exists(model_path):
        config_file = os.path.join(model_path, "config.json")
        if os.path.exists(config_file):
            return True
    return False

class StopOnTokens(StoppingCriteria):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.stop_ids = self.model.config.eos_token_id
        if not isinstance(self.stop_ids, (list, tuple)):
            self.stop_ids = [self.stop_ids]
        self.stop_ids_tensor = torch.tensor(self.stop_ids, device=self.model.device)
        
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        last_token = input_ids[0][-1]
        return last_token.item() in self.stop_ids

class QwenChat(commands.Cog):
    enable_history_limit = True  # 自動清除
    MAX_HISTORY_LENGTH = 5     # 最多保留幾輪對話
    
    def __init__(self, bot):
        self.bot = bot
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if check_model_path(BASE_MODEL_PATH):
            print("基礎模型路徑驗證成功")
        else:
            print(f"將從 HuggingFace 下載基礎模型: {BASE_MODEL_PATH}")
        print(f"正在載入基礎模型: {BASE_MODEL_PATH}")
        is_local_model = check_model_path(BASE_MODEL_PATH)
        load_kwargs = {}
        if is_local_model:
            load_kwargs["local_files_only"] = True
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True, **load_kwargs)
            print("分詞器載入成功")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,                      # 啟用 4-bit 量化
                bnb_4bit_quant_type="nf4",              # 使用 NF4 量化類型
                bnb_4bit_compute_dtype=torch.bfloat16,  # 計算時使用 bfloat16
                bnb_4bit_use_double_quant=True,         # 雙重量化 (開啟減少記憶體使用)
                bnb_4bit_quant_storage=torch.uint8,     # 量化權重儲存格式
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_PATH,
                dtype=torch.bfloat16,
                low_cpu_mem_usage=True, 
                trust_remote_code=True,
                quantization_config=quantization_config,
                device_map="auto",
                **load_kwargs
            )
            print("基礎模型載入成功")
            if LORA_PATH and os.path.exists(LORA_PATH):
                print(f"正在載入 LoRA 適配器: {LORA_PATH}")
                self.model = PeftModel.from_pretrained(self.model, LORA_PATH)
                print("LoRA 適配器載入成功")
            elif LORA_PATH:
                print(f"警告: LoRA 路徑不存在 {LORA_PATH}，使用基礎模型")
            else:
                print("未設定 LoRA 路徑，使用基礎模型")
            if hasattr(self.model, 'eval'):
                self.model.eval()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
        except Exception as e:
            print(f"模型載入失敗: {e}")
            if is_local_model:
                print("請檢查本地模型路徑是否正確")
            else:
                print("請檢查網路連接或嘗試使用本地模型")
            raise e
        if OPENCC_AVAILABLE:
            self.converter = OpenCC('s2t')
            print("OpenCC 繁簡轉換功能已啟用")
        else:
            self.converter = None
            print("OpenCC 未安裝，跳過繁簡轉換功能")
        self.history = []
        self.stop = StopOnTokens(self.model)
        
    @commands.command(aliases=["chat","CHAT"])
    async def Chat(self, ctx, *, message=None):
        if message is None and len(ctx.message.attachments) == 0:
            features = ["文字"]
            if WHISPER_AVAILABLE:
                features.append("音檔")
            features.append(".txt 檔案")
            await ctx.send(f"主人~使用 !Chat 請附上{' 或 '.join(features)}")
            return  
        if len(ctx.message.attachments) > 0:
            attachment = ctx.message.attachments[0]
            if attachment.filename.endswith('.txt'):
                try:
                    user_input = await self.handle_text_file(attachment)
                except Exception as e:
                    await ctx.send(f"主人~處理 .txt 檔案時發生錯誤: {e}")
                    return
            else:
                user_input = await self.handle_audio(ctx)
                if user_input is None:
                    return
        else:
            user_input = message
            if user_input is None:
                features = ["文字"]
                if WHISPER_AVAILABLE:
                    features.append("音檔")
                features.append(".txt 檔案")
                await ctx.send(f"主人~使用 !Chat 請附上{' 或 '.join(features)}")
                return  
        try:
            response_traditional = await self.generate_response(user_input)
        except Exception as e:
            await ctx.send(f"主人~處理請求時發生了錯誤: {e}")
            print(f"對話生成錯誤: {e}")
            return
        if len(response_traditional) <= 2000:
            await ctx.send(response_traditional)
        else:
            chunks = [response_traditional[i:i+2000] for i in range(0, len(response_traditional), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
    
    async def generate_response(self, user_input):
        self.history.append([user_input, ""])
        if self.enable_history_limit and len(self.history) > self.MAX_HISTORY_LENGTH:
            self.history.pop(0)
        messages = self._build_messages()
        with torch.no_grad():
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
        streamer = TextIteratorStreamer(
            tokenizer=self.tokenizer, 
            timeout=120, 
            skip_prompt=True, 
            skip_special_tokens=True
        )
        generate_kwargs = {
            "input_ids": model_inputs.input_ids,
            "attention_mask": model_inputs.attention_mask,
            "streamer": streamer,
            "max_new_tokens": 8192,
            "do_sample": True,
            "top_p": 0.9,
            "temperature": 0.3,
            "stopping_criteria": StoppingCriteriaList([self.stop]),
            "repetition_penalty": 1.05,
            "eos_token_id": self.model.config.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id,
            "use_cache": True,
        }
        with torch.no_grad():
            t = Thread(target=self.model.generate, kwargs=generate_kwargs)
            t.start()
        response_traditional = ""
        print(f"\n\n用戶: {user_input}")
        print("模型: ", end="", flush=True)
        for new_token in streamer:
            if new_token:
                if self.converter:
                    new_token_converted = self.converter.convert(new_token)
                else:
                    new_token_converted = new_token
                response_traditional += new_token_converted
                print(new_token_converted, end="", flush=True)
                self.history[-1][1] += new_token
        self.history[-1][1] = self.history[-1][1].strip()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return response_traditional
    
    def _build_messages(self):
        messages = []
        for idx, (user_msg, model_msg) in enumerate(self.history):
            if idx == len(self.history) - 1 and not model_msg:
                messages.append({"role": "user", "content": user_msg})
                break
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})
        return messages
            
    async def handle_audio(self, ctx):
        if not WHISPER_AVAILABLE:
            await ctx.send("主人~語音轉文字功能目前不可用，因為 Whisper 套件未安裝")
            return None
        model = whisper.load_model("base")
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):
            await ctx.send("主人~目前只支援 .mp3、.wav、.ogg 和 .flac 格式的音訊文件")
            return None
        folder_path = 'data/Audio'
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "A2T.mp3")
        try:
            await attachment.save(file_path)
        except Exception as e:
            await ctx.send(f"主人~發生了一點錯誤，請稍後再試: {e}")
            return None   
        result = model.transcribe(file_path)
        user_input = result['text']
        os.remove(file_path)
        return user_input
    
    async def handle_text_file(self, attachment):
        text = await attachment.read()
        user_input = text.decode('utf-8')
        return user_input

    @commands.command(aliases=["chatclear","CHATCLEAR"])
    async def ChatClear(self, ctx):
        self.clear_history()
        await ctx.send("長門櫻已重置記憶")
    
    @app_commands.command(name="chat", description="與長門櫻進行對話")
    @app_commands.describe(message="要發送給長門櫻的訊息")
    async def chat_slash(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        try:
            response_traditional = await self.generate_response(message)
            if len(response_traditional) <= 2000:
                await interaction.followup.send(response_traditional)
            else:
                chunks = [response_traditional[i:i+2000] for i in range(0, len(response_traditional), 2000)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
        except Exception as e:
            await interaction.followup.send(f"主人~處理請求時發生了錯誤: {e}")
            print(f"斜線指令對話生成錯誤: {e}")
    
    @app_commands.command(name="chatclear", description="清除長門櫻的對話記錄")
    async def chatclear_slash(self, interaction: discord.Interaction):
        self.clear_history()
        await interaction.response.send_message("長門櫻已重置記憶")

    def clear_history(self):
        """清空對話歷史並釋放記憶體"""
        self.history = []
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        print("Qwen3 已清除記憶和快取")
        
    @Chat.error
    async def qwen_error(self, ctx, error):
        await ctx.send(f"主人~處理請求時發生了錯誤: {error}")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(QwenChat(bot))
    print("Chat_Qwen3_NF4.py is ready")