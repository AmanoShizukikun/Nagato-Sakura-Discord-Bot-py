import discord
from discord.ext import commands
import os

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self,ctx):
        version = "1.5.λ"
        directory = 'assets/preview/'
        output_path = f"{directory}{version}.png"
        await ctx.send(f"# {version}")
        await ctx.send(file=discord.File(output_path))
        await ctx.send(f"### 重要變更 \n\n - AutoReply.py 升級為 AutoReply_v2.py 改為使用小型分類模型來回覆使用者，大幅提升可靠度 \n - 新增beta分類以及新增main_beta.py，能更直觀的看出哪些是測試功能哪些是一般功能 \n - 統一外掛 cogs 及 beta 的格式，更改代碼更舒服了")
        await ctx.send(f"### 新增功能 \n\n - !Version - 顯示當前機器人版本")
        await ctx.send(f"### 已知問題 \n\n - !play [網址] - Youtube 複數影片清單無法播放 \n - !play [網址] - Youtube 無法累加播放清單 \n - !Help - 幫助訊息過長無法傳出")
    
async def setup(bot):
    await bot.add_cog(Version(bot))
    print("Version.py is ready")