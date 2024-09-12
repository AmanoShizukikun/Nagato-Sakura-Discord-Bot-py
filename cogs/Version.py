import discord
from discord import app_commands
from discord.ext import commands

def create_version_message(version):
    version_message = f"# {version}\n"
    version_message += f"### 重要變更 \n\n - 【重大】儲存庫文件整理，將部分說明文件移至assets/docs中。\n - 【重大】資產調整，將原本的 png 改為 jpg 大幅減少了儲存庫容量並且提升了部分程式在 discord 的回應速度。\n - 【重大】Del.py 移動至 beta - 刪除權限過大個人認為不適合在一般模式使用他，避免惡意使用。\n - 【整合】Game.py 整合了 GuessingGame.py 及 SnakeGame.py 以後遊戲相關的功能將全部整合在這裡。\n - 【整合】Image.py 整合了 Image.py 及 SuperDeformed.py 以後圖像相關的功能將全部整合在這裡。\n - 【整合】Math.py 整合了 Math.py 及 PrimeNumber.py 以後計算相關的功能將全部整合在這裡。\n - 【移除】!Userinfo [用戶名稱] - 由於與 !Level 功能過於類似故將其移除。\n - 【移除】!Greeting [文字] - 該程式為 AutoReply.py 判斷的前身，他已經完美完成了他的任務是時候讓他走了。\n"
    version_message += f"### 新增功能 \n\n - 【更新】Del.py、Dice.py、Help.py、Ping.py、Vote.py 及 Youtube.py新增了/指令。\n - 【更新】Version.py - 更新為符合新版資產的輸出格式。\n - 【更新】Help.py - 刪除了按鈕並且重新改寫了鑲入內容。\n - 【更新】FestivalEvent.py - 新增更多彩蛋內容。\n - 【更新】CheckSMS.py - 現在能判斷出驗證碼簡訊後將驗證碼輸出，並且更新的模型版本。\n - 【修復】CheckSMS.py - 修復了將有小數點的訊息誤認成網址的錯誤。\n"
    version_message += f"### 已知問題 \n\n - 【錯誤】Youtube.py 使用/play [網址] 指令時，如果是播放清單會高機率報錯 (處理超時) ，建議使用播放清單時使用 !Play [網址] 來避免程式超時導致的報錯。\n"
    return version_message

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.directory = 'assets/preview/'
        self.version = "2.0.0"
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