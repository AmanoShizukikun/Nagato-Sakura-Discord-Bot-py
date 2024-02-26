import discord
from discord import app_commands
from discord.ext import commands

def create_version_message(version):
    version_message = f"# {version}\n"
    version_message += f"### 重要變更 \n\n - N/A"
    version_message += f"### 新增功能 \n\n - 【新增】!SuperDeformed - 可以隨機抽取長門櫻的Q版圖片。\n - 【更新】Choices.py、CustomCommands.py、Level.py、Translate.py、Version.py及Weather.py新增了/指令。\n - 【更新】!CheckSMS [文字] - 更新模型版本，現在可以判斷簡訊的類別、簡訊中的電話、簡訊中的網址並且能檢測網址的安全性。\n - 【測試】!SnakeGame - 玩貪吃蛇遊戲，!SnakeGameReset - 重置貪吃蛇遊戲。"
    version_message += f"### 已知問題 \n\n - N/A"
    return version_message

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.directory = 'assets/preview/'
        self.version = "1.6.1"
        self.output_path = f"{self.directory}{self.version}.jpg"
        
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