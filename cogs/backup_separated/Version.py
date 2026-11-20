import discord
from discord import app_commands
from discord.ext import commands
import datetime
import platform
import psutil
import sys

def create_version_message(version):
    version_message = f"# 🌸 長門櫻 {version} 🌸\n"
    version_message += f"（輕輕行禮）主人～這是長門櫻目前的版本資訊呢❤️\n\n"
    version_message += f"### 🎊 重要變更 \n\n"
    version_message += f" - 🌟 **【重大】** 儲存庫文件整理，將部分說明文件移至assets/docs中。\n"
    version_message += f" - 🎨 **【重大】** 資產調整，將原本的 png 改為 jpg 大幅減少了儲存庫容量並且提升了部分程式在 discord 的回應速度。\n"
    version_message += f" - 🔒 **【重大】** Del.py 移動至 beta - 刪除權限過大個人認為不適合在一般模式使用他，避免惡意使用。\n"
    version_message += f" - 🔧 **【整合】** Game.py 整合了 GuessingGame.py 及 SnakeGame.py 以後遊戲相關的功能將全部整合在這裡。\n"
    version_message += f" - 🖼️ **【整合】** Image.py 整合了 Image.py 及 SuperDeformed.py 以後圖像相關的功能將全部整合在這裡。\n"
    version_message += f" - 🧮 **【整合】** Math.py 整合了 Math.py 及 PrimeNumber.py 以後計算相關的功能將全部整合在這裡。\n"
    version_message += f" - ❌ **【移除】** !Userinfo [用戶名稱] - 由於與 !Level 功能過於類似故將其移除。\n"
    version_message += f" - 🗑️ **【移除】** !Greeting [文字] - 該程式為 AutoReply.py 判斷的前身，他已經完美完成了他的任務是時候讓他走了。\n\n"
    
    version_message += f"### ✨ 新增功能 \n\n"
    version_message += f" - 🔄 **【更新】** Del.py、Dice.py、Help.py、Ping.py、Vote.py 及 Youtube.py新增了/指令。\n"
    version_message += f" - 📋 **【更新】** Version.py - 更新為符合新版資產的輸出格式。\n"
    version_message += f" - 📖 **【更新】** Help.py - 刪除了按鈕並且重新改寫了鑲入內容。\n"
    version_message += f" - 🎉 **【更新】** FestivalEvent.py - 新增更多彩蛋內容。\n"
    version_message += f" - 🛡️ **【更新】** CheckSMS.py - 現在能判斷出驗證碼簡訊後將驗證碼輸出，並且更新的模型版本。\n"
    version_message += f" - 🔧 **【修復】** CheckSMS.py - 修復了將有小數點的訊息誤認成網址的錯誤。\n\n"
    
    version_message += f"### ⚠️ 已知問題 \n\n"
    version_message += f" - 🐛 **【錯誤】** Youtube.py 使用/play [網址] 指令時，如果是播放清單會高機率報錯 (處理超時) ，建議使用播放清單時使用 !Play [網址] 來避免程式超時導致的報錯。\n\n"
    
    return version_message

def get_system_info():
    """獲取系統資訊"""
    try:
        # 系統基本資訊
        system = platform.system()
        release = platform.release()
        version = platform.version()
        architecture = platform.architecture()[0]
        
        # Python 版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # 記憶體使用情況
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)  # GB
        memory_used = round(memory.used / (1024**3), 2)   # GB
        memory_percent = memory.percent
        
        # CPU 資訊
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        return {
            "system": f"{system} {release}",
            "architecture": architecture,
            "python_version": python_version,
            "memory_total": memory_total,
            "memory_used": memory_used,
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count
        }
    except Exception as e:
        return None

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.directory = 'assets/preview/'
        self.version = "2.0.0"
        self.output_path = f"{self.directory}{self.version}.jpg"
        
    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self, ctx):
        version_message = create_version_message(self.version)
        
        # 創建版本資訊嵌入訊息
        version_embed = discord.Embed(
            title="📋 系統資訊",
            description="（認真地整理資料）這裡是長門櫻的詳細系統資訊喔～",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        # 機器人基本資訊
        version_embed.add_field(
            name="🤖 機器人資訊",
            value=f"**版本：** {self.version}\n**名稱：** {self.bot.user.name}\n**ID：** {self.bot.user.id}",
            inline=True
        )
        
        # Discord.py 版本
        version_embed.add_field(
            name="📚 框架版本",
            value=f"**discord.py：** {discord.__version__}\n**延遲：** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # 伺服器統計
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members()))
        version_embed.add_field(
            name="📊 服務統計",
            value=f"**伺服器數：** {guild_count}\n**用戶數：** {user_count}",
            inline=True
        )
        
        # 系統資訊
        system_info = get_system_info()
        if system_info:
            version_embed.add_field(
                name="💻 系統資訊",
                value=f"**系統：** {system_info['system']}\n**架構：** {system_info['architecture']}\n**Python：** {system_info['python_version']}",
                inline=True
            )
            
            version_embed.add_field(
                name="🧠 記憶體使用",
                value=f"**使用：** {system_info['memory_used']}GB / {system_info['memory_total']}GB\n**使用率：** {system_info['memory_percent']}%",
                inline=True
            )
            
            version_embed.add_field(
                name="⚡ CPU 使用",
                value=f"**使用率：** {system_info['cpu_percent']}%\n**核心數：** {system_info['cpu_count']}",
                inline=True
            )
        
        version_embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        version_embed.timestamp = datetime.datetime.now()
        
        # 先發送版本訊息，再發送系統資訊
        await ctx.send(version_message, file=discord.File(self.output_path))
        await ctx.send(embed=version_embed)
        
    @app_commands.command(name="version", description="!Version - 顯示長門櫻當前版本")
    async def version(self, interaction: discord.Interaction):
        version_message = create_version_message(self.version)
        
        # 創建版本資訊嵌入訊息
        version_embed = discord.Embed(
            title="📋 系統資訊",
            description="（認真地整理資料）這裡是長門櫻的詳細系統資訊喔～",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        # 機器人基本資訊
        version_embed.add_field(
            name="🤖 機器人資訊",
            value=f"**版本：** {self.version}\n**名稱：** {self.bot.user.name}\n**ID：** {self.bot.user.id}",
            inline=True
        )
        
        # Discord.py 版本
        version_embed.add_field(
            name="📚 框架版本",
            value=f"**discord.py：** {discord.__version__}\n**延遲：** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # 伺服器統計
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members()))
        version_embed.add_field(
            name="📊 服務統計",
            value=f"**伺服器數：** {guild_count}\n**用戶數：** {user_count}",
            inline=True
        )
        
        # 系統資訊
        system_info = get_system_info()
        if system_info:
            version_embed.add_field(
                name="💻 系統資訊",
                value=f"**系統：** {system_info['system']}\n**架構：** {system_info['architecture']}\n**Python：** {system_info['python_version']}",
                inline=True
            )
            
            version_embed.add_field(
                name="🧠 記憶體使用",
                value=f"**使用：** {system_info['memory_used']}GB / {system_info['memory_total']}GB\n**使用率：** {system_info['memory_percent']}%",
                inline=True
            )
            
            version_embed.add_field(
                name="⚡ CPU 使用",
                value=f"**使用率：** {system_info['cpu_percent']}%\n**核心數：** {system_info['cpu_count']}",
                inline=True
            )
        
        version_embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        version_embed.timestamp = datetime.datetime.now()
        
        # 先發送版本訊息，再發送系統資訊
        await interaction.response.send_message(version_message, file=discord.File(self.output_path))
        await interaction.followup.send(embed=version_embed)
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Version(bot))
    print("Version.py is ready")