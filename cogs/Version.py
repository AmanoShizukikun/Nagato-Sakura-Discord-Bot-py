import discord
from discord.ext import commands

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self,ctx):
        version = "1.6.0"
        directory = 'assets/preview/'
        output_path = f"{directory}{version}.png"
        await ctx.send(f"# {version}")
        await ctx.send(file=discord.File(output_path))
        await ctx.send(f"### 重要變更 \n\n - DM.py 及 Tarot.py 新增了/指令現在能更直觀的調用指令了 \n - main_beta.py 新增了 載入指令程式檔案、卸載指令檔案、重新載入程式檔案、載入斜線指令 \n - 精簡了部分程式的行數提高了效率")
        await ctx.send(f"### 新增功能 \n\n - !FestivalEvent - 當特殊的日子來臨之時會有彩蛋")
        await ctx.send(f"### 已知問題 \n\n - N/A")
    
async def setup(bot):
    await bot.add_cog(Version(bot))
    print("Version.py is ready")