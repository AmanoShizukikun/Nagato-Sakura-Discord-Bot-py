import discord
from discord import app_commands
from discord.ext import commands
from threading import Thread
from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer, AutoModel, BitsAndBytesConfig
from opencc import OpenCC
import torch
import whisper
import os

class StopOnTokens(StoppingCriteria):
    def __init__(self, model):
        super().__init__()
        self.eos_token_id = [model.config.eos_token_id]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in self.eos_token_id:
            if input_ids[0][-1] == stop_id:
                return True
        return False

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True, encode_special_tokens=True)
        self.model = AutoModel.from_pretrained("THUDM/chatglm3-6b", torch_dtype=torch.bfloat16, low_cpu_mem_usage=True, trust_remote_code=True, quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float32, bnb_4bit_quant_type="fp4", bnb_4bit_use_double_quant=True, bnb_4bit_quant_storage=torch.uint8)).eval()
        self.converter = OpenCC('s2t')
        self.history = []
        self.stop = StopOnTokens(self.model)

    @commands.command(aliases=["chat", "CHAT"])
    async def Chat(self, ctx, *, message=None):
        if message is None and len(ctx.message.attachments) == 0:
            await ctx.send("主人~使用 !Chat 請附上文字或音檔")
            return

        if len(ctx.message.attachments) > 0:
            user_input = await self.handle_audio(ctx)
            if user_input is None:
                return
        else:
            user_input = message
            if user_input is None:
                await ctx.send("主人~使用 !Chat 請附上文字或音檔")
                return

        self.history.append([user_input, ""])
        messages = []
        for idx, (user_msg, model_msg) in enumerate(self.history):
            if idx == len(self.history) - 1 and not model_msg:
                messages.append({"role": "user", "content": user_msg})
                break
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})

        model_inputs = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True, return_tensors="pt").to(self.model.device)
        streamer = TextIteratorStreamer(tokenizer=self.tokenizer, timeout=60, skip_prompt=True, skip_special_tokens=True)
        generate_kwargs = {
            "input_ids": model_inputs,
            "streamer": streamer,
            "max_new_tokens": 8192,
            "do_sample": True,
            "top_p": 0.8,
            "temperature": 0.6,
            "stopping_criteria": StoppingCriteriaList([self.stop]),
            "repetition_penalty": 1.2,
            "eos_token_id": self.model.config.eos_token_id,
        }

        t = Thread(target=self.model.generate, kwargs=generate_kwargs)
        t.start()
        response_traditional = ""
        print("模型: ", end="", flush=True)
        for new_token in streamer:
            if new_token:
                new_token_converted = self.converter.convert(new_token)
                response_traditional += new_token_converted
                print(new_token_converted, end="", flush=True)
                self.history[-1][1] += new_token
        self.history[-1][1] = self.history[-1][1].strip()
        response = f"{response_traditional}"
        if len(response) <= 2000:
            await ctx.send(response)
        else:
            chunks = [response_traditional[i:i + 2000] for i in range(0, len(response_traditional), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
        print("")
        return response_traditional

    async def handle_audio(self, ctx):
        model = whisper.load_model("base")
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):
            await ctx.send("主人~目前只支援 .mp3、.wav、.ogg 和 .flac 格式的音訊文件")
            return None
        folder_path = 'data/Audio'
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "A2T.wav")
        try:
            await attachment.save(file_path)
        except Exception as e:
            await ctx.send(f"主人~發生了一點錯誤，請稍後再試: {e}")
            return None

        result = model.transcribe(file_path)
        user_input = result['text']
        os.remove(file_path)
        return user_input

    @commands.command(aliases=["chatclear", "CHATCLEAR"])
    async def ChatClear(self, ctx):
        self.history = []
        await ctx.send("長門櫻已重置記憶")

    @app_commands.command(name="chatclear", description="!ChatCllear - 清除長門櫻的對話記錄")
    async def ping(self, interaction: discord.Interaction):
        self.history = []
        await interaction.response.send_message("長門櫻已重置記憶")

    @Chat.error
    async def chat_error(self, ctx, error):
        await ctx.send(f"主人~處理請求時發生了錯誤: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Chat(bot))
    print("ChatV2_GLM3_INT4.py is ready")
