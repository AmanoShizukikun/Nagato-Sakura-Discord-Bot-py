import discord
from discord.ext import commands
from moviepy import *
import os

class Video(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_directory(self):
        directory = 'data/Video/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    @commands.command(aliases=["VTG","videotogif","VIDEOTOGIF"])
    async def VideoToGif(self, ctx, *args):
        if not ctx.message.attachments:
            await ctx.send("請上傳影片檔")
            return

        width, height = 360, 180
        start_time, end_time, fps = 0, 5, 24

        if len(args) >= 2:
            try:
                width = int(args[0])
                height = int(args[1])
            except ValueError:
                await ctx.send("請提供有效的數字參數")
                return

        if len(args) >= 4:
            try:
                start_time = int(args[2])
                end_time = int(args[3])
            except ValueError:
                await ctx.send("請提供有效的數字參數")
                return

        if len(args) >= 5:
            try:
                fps = int(args[4])
            except ValueError:
                await ctx.send("請提供有效的數字參數")
                return

        try:
            directory = await self.create_directory()

            for attachment in ctx.message.attachments:
                if attachment.content_type.startswith('video'):
                    filename = f"{directory}{attachment.filename}"
                    await attachment.save(filename)

                    video_clip = VideoFileClip(filename)
                    output = (
                        video_clip.resize((width, height))
                        .subclip(start_time, end_time)
                        .set_fps(fps)
                        .set_duration(end_time - start_time)
                    )

                    output_path = f"{directory}output.gif"
                    output.write_gif(output_path)

                    await ctx.send(file=discord.File(output_path))
                    print('ok')
                    return

            await ctx.send("未找到有效的影片檔")
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")

async def setup(bot):
    await bot.add_cog(Video(bot))
    print("VideoToGif.py is ready")