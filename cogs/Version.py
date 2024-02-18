import discord
from discord import app_commands
from discord.ext import commands

def create_version_message(version):
    version_message = f"# {version}\n"
    version_message += f"### 重要變更 \n\n - DM.py 及 Tarot.py 新增了/指令現在能更直觀的調用指令了 \n - main_beta.py 新增了 載入指令程式檔案、卸載指令檔案、重新載入程式檔案、載入斜線指令 \n - 精簡了部分程式的行數提高了效率\n"
    version_message += f"### 新增功能 \n\n - !FestivalEvent - 當特殊的日子來臨之時會有彩蛋\n"
    version_message += f"### 已知問題 \n\n - N/A"
    return version_message

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.directory = 'assets/preview/'
        self.version = "1.6.0"
        self.output_path = f"{self.directory}{self.version}.png"
        
    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self, ctx):
        version_message = create_version_message(self.version)
        await ctx.send(version_message, file=discord.File(self.output_path))
        
    @app_commands.command(name="version", description="!Version - 顯示長門櫻當前版本")
    async def version(self, interaction: discord.Interaction):
        version_message = create_version_message(self.version)
        await interaction.response.send_message(version_message, file=discord.File(self.output_path))
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Version(bot))
    print("Version.py is ready")