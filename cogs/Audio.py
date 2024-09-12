import discord
from discord.ext import commands
from pydub import AudioSegment 
from io import BytesIO
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['audioinfo', 'AUDIOINFO'])
    async def AudioInfo(self, ctx):
        if ctx.message.attachments and ctx.message.attachments[0].filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            attachment = ctx.message.attachments[0]
            audio_bytes = await attachment.read()
            audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format=attachment.filename.split('.')[-1])
            duration_seconds = audio_segment.duration_seconds
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bitrate = audio_segment.frame_rate
            await ctx.send(f"聲道數量: {audio_segment.channels}, 長度: {int(hours)}:{int(minutes)}:{int(seconds)}, 位元率: {bitrate} bps")
            wave_image_path = self.visualize_waveform(audio_bytes, attachment.filename)
            wave_image_file = discord.File(wave_image_path)
            await ctx.send("聲波圖形：", file=wave_image_file)

    def visualize_waveform(self, audio_bytes, filename):
        audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format=filename.split('.')[-1])
        fig, ax = plt.subplots()
        audio_samples = audio_segment.get_array_of_samples()
        plt.specgram(audio_samples, Fs=audio_segment.frame_rate, cmap='viridis', aspect='auto')
        plt.title("Spectrogram")
        plt.xlabel("Time")
        plt.ylabel("Frequency")
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = BytesIO()
        canvas.print_png(buf)
        buf.seek(0)

        image_path = os.path.join('data/Audio', 'spectrogram.png')
        with open(image_path, 'wb') as f:
            f.write(buf.read())

        plt.close(fig) 
        return image_path
            
    @commands.command(aliases=['audioreverse', 'AUDIOREVERSE'])
    async def AudioReverse(self, ctx):
        if ctx.message.attachments and ctx.message.attachments[0].filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            attachment = ctx.message.attachments[0]
            audio_bytes = await attachment.read()
            audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format=attachment.filename.split('.')[-1])
            reversed_audio = audio_segment.reverse()
            folder_path = 'data/Audio'
            os.makedirs(folder_path, exist_ok=True)
            reversed_output_path = os.path.join(folder_path, 'reversed_output.mp3')
            reversed_audio.export(reversed_output_path, format='mp3')
            reversed_output_file = discord.File(reversed_output_path)
            await ctx.send("長門櫻已將聲音反轉，這是反轉後的聲音檔：", file=reversed_output_file)

    @commands.command(aliases=['audiospeed', 'AUDIOSPEED'])
    async def AudioSpeed(self, ctx, speed: float):
        if ctx.message.attachments and ctx.message.attachments[0].filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            attachment = ctx.message.attachments[0]
            audio_bytes = await attachment.read()
            audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format=attachment.filename.split('.')[-1])
            speeded_audio = audio_segment.speedup(playback_speed=speed)
            folder_path = 'data/Audio'
            os.makedirs(folder_path, exist_ok=True)
            speeded_output_path = os.path.join(folder_path, 'speeded_output.mp3')
            speeded_audio.export(speeded_output_path, format='mp3')
            speeded_output_file = discord.File(speeded_output_path)
            await ctx.send(f"長門櫻已將聲音撥放速度調整為 {speed} 倍，這是調整速度後的聲音檔：", file=speeded_output_file)

    @commands.command(aliases=['audiobit', 'AUDIOBIT'])
    async def AudioBit(self, ctx, bit: int):
        if ctx.message.attachments and ctx.message.attachments[0].filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            attachment = ctx.message.attachments[0]
            audio_bytes = await attachment.read()
            audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format=attachment.filename.split('.')[-1])
            bit_adjusted_audio = audio_segment.set_sample_width(bit // 8)
            bit_adjusted_audio = bit_adjusted_audio.low_pass_filter(4000)
            folder_path = 'data/Audio'
            os.makedirs(folder_path, exist_ok=True)
            bit_adjusted_output_path = os.path.join(folder_path, f'bit_adjusted_output_{bit}bit.mp3')
            bit_adjusted_audio.export(bit_adjusted_output_path, format='mp3')
            bit_adjusted_output_file = discord.File(bit_adjusted_output_path)
            await ctx.send(f"長門櫻已將聲音位元數調整為 {bit} 位，這是調整位元數後的聲音檔：", file=bit_adjusted_output_file)
            
    @AudioInfo.error
    async def audio_info_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!AudioInfo指令時要附上聲音檔哦。")
            
    @AudioReverse.error
    async def audio_reverse_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!AudioReverse指令時要附上聲音檔哦。")
    
    @AudioSpeed.error
    async def audio_speed_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!AudioSpeed指令時的正確方法為!AudioSpeed [倍速] 並附上聲音檔哦。")
            
    @AudioBit.error
    async def audio_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用這個指令時要附上合適的參數哦。")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("主人~出現了一些問題，請稍後再試。")

async def setup(bot):
    await bot.add_cog(Audio(bot))
    print("Audio.py is ready")