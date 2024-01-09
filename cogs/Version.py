import discord
from discord.ext import commands
import os

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self,ctx):
        version = "1.5.μ"
        directory = 'assets/preview/'
        output_path = f"{directory}{version}.png"
        await ctx.send(f"# {version}")
        await ctx.send(file=discord.File(output_path))
        await ctx.send(f"### 重要變更 \n\n - 刪除了Music.py改為Youtube.py(不再支持streetvoice)，修正了Youtube 複數影片清單無法播放及Youtube 無法累加播放清單的問題 \n - 修正了並且改善了!Help - 幫助訊息過長無法傳出的問題")
        await ctx.send(f"### 新增功能 \n\n - !List - 長門櫻顯示撥放清單 \n - !Skip [數字] - 跳過 [數字] 首歌")
        await ctx.send(f"### 已知問題 \n\n - N/A ")
    
async def setup(bot):
    await bot.add_cog(Version(bot))
    print("Version.py is ready")