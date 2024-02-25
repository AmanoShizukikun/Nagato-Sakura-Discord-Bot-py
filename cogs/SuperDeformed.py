import discord
from discord.ext import commands
import random
import os

class SuperDeformed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["superdeformed","SD","ChibiCharacter","chibicharacter","Chibi","chibi"])
    async def SuperDeformed(self, ctx):
        superdeformed_folder = os.path.abspath(f'./assets/sticker/')
        if os.path.exists(superdeformed_folder):
            superdeformed_images = [f for f in os.listdir(superdeformed_folder) if f.endswith('.jpg') or f.endswith('.png')]
            if superdeformed_images:
                image_name = random.choice(superdeformed_images)
                image_path = os.path.join(superdeformed_folder, image_name)
                with open(image_path, 'rb') as f:
                    picture = discord.File(f)
                await ctx.send(file=picture)
            else:
                await ctx.send(f"抱歉啊~主人!長門櫻找不到貼圖。")
        else:
            await ctx.send(f"抱歉啊~主人!長門櫻找不到貼圖的資料夾。")
        
async def setup(bot):
    await bot.add_cog(SuperDeformed(bot))
    print("SuperDeformed.py is ready")
