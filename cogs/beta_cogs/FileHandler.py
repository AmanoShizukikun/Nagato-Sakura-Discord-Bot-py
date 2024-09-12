import discord
from discord.ext import commands
import os

class FileHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if isinstance(message.channel, discord.TextChannel):
            if message.attachments and self.bot.user.mentioned_in(message):
                for attachment in message.attachments:
                    if attachment.content_type.startswith('image'):
                        await self.save_image(attachment)
                        await message.channel.send(f"長門櫻已保存主人的照片：data/downloaded_images/{attachment.filename}")
                        print(f"圖片已下載至：data/downloaded_images/{attachment.filename}")
                        
                    elif attachment.content_type.startswith('text'):
                        await self.save_text(attachment)
                        await message.channel.send(f"長門櫻已保存主人的文件：data/downloaded_videos/{attachment.filename}")
                        print(f"文件已下載至：data/downloaded_images/{attachment.filename}")
                        
                    elif attachment.content_type.startswith('audio'):
                        await self.save_audio(attachment)
                        await message.channel.send(f"長門櫻已保存主人的聲音：data/downloaded_audio/{attachment.filename}")
                        print(f"聲音已下載至：data/downloaded_audio/{attachment.filename}")
                        
                    elif attachment.content_type.startswith('video'):
                        await self.save_video(attachment)
                        await message.channel.send(f"長門櫻已保存主人的影片：data/downloaded_videos/{attachment.filename}")
                        print(f"影片已下載至：data/downloaded_videos/{attachment.filename}")
    
        elif isinstance(message.channel, discord.DMChannel):
            if message.attachments and self.bot.user.mentioned_in(message):
                for attachment in message.attachments:
                    if attachment.content_type.startswith('image'):
                        await self.save_image(attachment)
                        await message.channel.send(f"長門櫻已保存主人的照片：data/downloaded_images/{attachment.filename}")
                        print(f"圖片已下載至：data/downloaded_images/{attachment.filename}")
                        
                    elif attachment.content_type.startswith('text'):
                        await self.save_text(attachment)
                        await message.channel.send(f"長門櫻已保存主人的文件：data/downloaded_videos/{attachment.filename}")
                        print(f"文件已下載至：data/downloaded_images/{attachment.filename}")
                        
                    elif attachment.content_type.startswith('audio'):
                        await self.save_audio(attachment)
                        await message.channel.send(f"長門櫻已保存主人的聲音：data/downloaded_audio/{attachment.filename}")
                        print(f"聲音已下載至：data/downloaded_audio/{attachment.filename}")
                        
                    elif attachment.content_type.startswith('video'):
                        await self.save_video(attachment)
                        await message.channel.send(f"長門櫻已保存主人的影片：data/downloaded_videos/{attachment.filename}")
                        print(f"影片已下載至：data/downloaded_videos/{attachment.filename}")
    
    async def save_text(self, attachment):
        download_dir = "data/downloaded_text"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        download_path = f"{download_dir}/{attachment.filename}"
        await attachment.save(download_path)
            
    async def save_image(self, attachment):
        # 下載圖片並儲存在指定資料夾
        download_dir = "data/downloaded_images"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        download_path = f"{download_dir}/{attachment.filename}"
        await attachment.save(download_path)
        
    async def save_audio(self, attachment):
        # 下載聲音並儲存在指定資料夾
        download_dir = "data/downloaded_audio"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        download_path = f"{download_dir}/{attachment.filename}"
        await attachment.save(download_path)
        
    async def save_video(self, attachment):
        # 下載影片並儲存在指定資料夾
        download_dir = "data/downloaded_videos"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        download_path = f"{download_dir}/{attachment.filename}"
        await attachment.save(download_path)

async def setup(bot):
    await bot.add_cog(FileHandler(bot))
    print("FileHandler.py is ready")
