import discord
from discord.ext import commands
import whisper
import os

class AudioToText(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = whisper.load_model("base", device="cpu")

    @commands.command()
    async def A2T(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("主人~使用 !A2T 請附上音檔")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            await ctx.send("主人~請上傳正確的音檔格式")
            return

        folder_path = 'data/Audio'
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "A2T.wav")
        
        try:
            await attachment.save(file_path)
        except Exception as e:
            await ctx.send(f"主人~發生了一點錯誤，請稍後再試: {e}")
            return

        audio = whisper.pad_or_trim(whisper.load_audio(file_path))
        result = self.model.transcribe(file_path)
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(mel)
        detected_language = max(probs, key=probs.get)
        await ctx.send(f"語言: [ {detected_language} ]\n結果: {result['text']}")
        os.remove(file_path)

async def setup(bot):
    await bot.add_cog(AudioToText(bot))
    print("AudioToText.py is ready")
