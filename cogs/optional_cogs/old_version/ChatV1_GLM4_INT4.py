import discord
from discord import app_commands
from discord.ext import commands
from transformers import AutoTokenizer, AutoModel, BitsAndBytesConfig
from opencc import OpenCC
import torch
import whisper
import os

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("THUDM/glm-4-9b-chat", trust_remote_code=True, encode_special_tokens=True)
        self.model = AutoModel.from_pretrained("THUDM/glm-4-9b-chat", torch_dtype=torch.bfloat16, low_cpu_mem_usage=True, trust_remote_code=True, quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float32, bnb_4bit_quant_type="fp4", bnb_4bit_use_double_quant=True, bnb_4bit_quant_storage=torch.uint8)).eval()
        self.converter = OpenCC('s2t')
        self.history = []
        self.past_key_values = None
        
    @commands.command(aliases=["chat","CHAT"])
    async def Chat(self, ctx, *, message=None):
        if message is None and len(ctx.message.attachments) == 0:
            await ctx.send("主人~使用 !Chat 請附上文字或音檔或 .txt 檔案")
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
                await ctx.send("主人~使用 !Chat 請附上文字或音檔或 .txt 檔案")
                return
            
        response_traditional = ""
        print("模型: ", end="", flush=True)
        try:
            with torch.no_grad():
                for response, self.history, self.past_key_values in self.model.stream_chat(self.tokenizer, user_input, self.history, past_key_values=self.past_key_values, max_length=8192, top_p=0.8, temperature=0.6, return_past_key_values=True):
                    new_token = self.converter.convert(response[len(response_traditional):])
                    response_traditional += new_token
                    print(new_token, end="", flush=True)
        except Exception as e:
            print(f"\n發生錯誤: {e}")
        print()

        response = f"{response_traditional}"
        if len(response) <= 2000:
            await ctx.send(response)
        else:
            chunks = [response_traditional[i:i+2000] for i in range(0, len(response_traditional), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
            
    async def handle_audio(self, ctx):
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
        self.history = []  
        self.past_key_values = None
        await ctx.send("長門櫻已重置記憶")
    
    @app_commands.command(name="chatclear", description="!ChatCllear - 清除長門櫻的對話記錄")
    async def ping(self, interaction: discord.Interaction):
        self.history = []
        self.past_key_values = None
        await interaction.response.send_message("長門櫻已重置記憶")
    
    @Chat.error
    async def chat_error(self, ctx, error):
        await ctx.send(f"主人~處理請求時發生了錯誤: {error}")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Chat(bot))
    print("ChatV1_GLM4_INT4.py is ready")
