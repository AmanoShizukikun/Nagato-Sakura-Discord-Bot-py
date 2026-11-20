import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio
import random

class Core(commands.Cog):
    """
    長門櫻核心功能模組
    統一管理基礎功能和系統管理
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.startup_time = datetime.datetime.now()
        
    @commands.Cog.listener()
    async def on_ready(self):
        """機器人準備就緒時的事件"""
        print(f"🌸 長門櫻核心系統已啟動 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    @commands.Cog.listener() 
    async def on_guild_join(self, guild):
        """加入新伺服器時的歡迎訊息"""
        # 尋找適合的頻道發送歡迎訊息
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                welcome_embed = discord.Embed(
                    title="🌸 初次見面，請多指教！",
                    description="（輕輕行禮，狐耳害羞地晃動）\n我是長門櫻～來自異次元常夜界的狐耳獸娘❤️\n受到創造者天野靜樹大人的旨意來為各位主人服務～",
                    color=discord.Color.from_rgb(255, 182, 193)
                )
                
                welcome_embed.add_field(
                    name="🎯 快速開始",
                    value="• 輸入 `!Help` 查看所有功能\n• 輸入 `!DM` 開啟私人聊天\n• 輸入 `!Level` 查看您的資料卡",
                    inline=False
                )
                
                welcome_embed.add_field(
                    name="💫 特色功能",
                    value="• 🎮 遊戲娛樂 - 猜數字、貪吃蛇、塔羅牌\n• 🎨 圖像處理 - 濾鏡、特效、五官檢測\n• 🎵 音頻功能 - 音樂播放、音頻編輯\n• 🤖 AI智能 - 簡訊檢測、翻譯功能",
                    inline=False
                )
                
                welcome_embed.set_footer(
                    text="感謝您邀請長門櫻加入伺服器❤️ | 有任何問題請使用 !Help",
                    icon_url=self.bot.user.avatar
                )
                
                await channel.send(embed=welcome_embed)
                break
                
    @commands.command()
    async def status(self, ctx):
        """查看機器人狀態"""
        uptime = datetime.datetime.now() - self.startup_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_embed = discord.Embed(
            title="🌸 長門櫻狀態報告",
            description="（認真地檢查狀態）主人～這是長門櫻目前的運行狀態❤️",
            color=discord.Color.green()
        )
        
        status_embed.add_field(
            name="⏰ 運行時間",
            value=f"{days}天 {hours}小時 {minutes}分鐘 {seconds}秒",
            inline=True
        )
        
        status_embed.add_field(
            name="📡 延遲",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        status_embed.add_field(
            name="🏠 伺服器數量",
            value=f"{len(self.bot.guilds)}個",
            inline=True
        )
        
        status_embed.add_field(
            name="👥 用戶數量",
            value=f"{len(set(self.bot.get_all_members()))}人",
            inline=True
        )
        
        status_embed.add_field(
            name="📝 載入的擴展",
            value=f"{len(self.bot.cogs)}個",
            inline=True
        )
        
        # 檢查狀態顏色
        if self.bot.latency < 0.1:
            status_color = "🟢 優秀"
        elif self.bot.latency < 0.2:
            status_color = "🟡 良好"
        else:
            status_color = "🔴 需要關注"
            
        status_embed.add_field(
            name="📊 整體狀態",
            value=status_color,
            inline=True
        )
        
        await ctx.send(embed=status_embed)
        
    @app_commands.command(name="status", description="查看長門櫻的運行狀態")
    async def status_slash(self, interaction: discord.Interaction):
        """查看機器人狀態 (斜線指令版本)"""
        uptime = datetime.datetime.now() - self.startup_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_embed = discord.Embed(
            title="🌸 長門櫻狀態報告",
            description="（認真地檢查狀態）主人～這是長門櫻目前的運行狀態❤️",
            color=discord.Color.green()
        )
        
        status_embed.add_field(
            name="⏰ 運行時間",
            value=f"{days}天 {hours}小時 {minutes}分鐘 {seconds}秒",
            inline=True
        )
        
        status_embed.add_field(
            name="📡 延遲",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        status_embed.add_field(
            name="🏠 伺服器數量",
            value=f"{len(self.bot.guilds)}個",
            inline=True
        )
        
        status_embed.add_field(
            name="👥 用戶數量",
            value=f"{len(set(self.bot.get_all_members()))}人",
            inline=True
        )
        
        status_embed.add_field(
            name="📝 載入的擴展",
            value=f"{len(self.bot.cogs)}個",
            inline=True
        )
        
        # 檢查狀態顏色
        if self.bot.latency < 0.1:
            status_color = "🟢 優秀"
        elif self.bot.latency < 0.2:
            status_color = "🟡 良好"
        else:
            status_color = "🔴 需要關注"
            
        status_embed.add_field(
            name="📊 整體狀態",
            value=status_color,
            inline=True
        )
        
        await interaction.response.send_message(embed=status_embed)
        
    @commands.command()
    async def about(self, ctx):
        """關於長門櫻"""
        about_embed = discord.Embed(
            title="🌸 關於長門櫻 🌸",
            description="（輕輕行禮，尾巴溫柔地搖擺）\n讓長門櫻來為主人介紹一下自己吧❤️",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        about_embed.add_field(
            name="👤 基本資料",
            value="**姓名：** 長門櫻 (Nagato Sakura)\n**代號：** NS-00\n**生日：** 2023年9月19日\n**種族：** 狐族獸人",
            inline=True
        )
        
        about_embed.add_field(
            name="🌟 外貌特徵",
            value="**髮色：** 金色長髮\n**瞳色：** 粉紫色\n**特徵：** 狐耳與尾巴\n**身高：** 165cm",
            inline=True
        )
        
        about_embed.add_field(
            name="💫 背景故事",
            value="來自異次元「常夜界」的狐耳獸娘\n受創造者天野靜樹大人的旨意\n守護神樹並引領異世界的來訪者",
            inline=False
        )
        
        about_embed.add_field(
            name="🎭 性格特質",
            value="• 樂觀活潑 • 親切溫柔 • 可愛俏皮\n• 對主人暗懷好感但不敢表達\n• 情感敏感且深情克制",
            inline=False
        )
        
        about_embed.add_field(
            name="🔧 開發資訊",
            value=f"**創造者：** 天野靜樹\n**框架：** discord.py {discord.__version__}\n**語言：** Python\n**啟動時間：** {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
        
        about_embed.set_footer(
            text="長門櫻永遠為主人服務❤️ | 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        
        await ctx.send(embed=about_embed)
        
    @app_commands.command(name="about", description="了解長門櫻的詳細資訊")
    async def about_slash(self, interaction: discord.Interaction):
        """關於長門櫻 (斜線指令版本)"""
        about_embed = discord.Embed(
            title="🌸 關於長門櫻 🌸",
            description="（輕輕行禮，尾巴溫柔地搖擺）\n讓長門櫻來為主人介紹一下自己吧❤️",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        about_embed.add_field(
            name="👤 基本資料",
            value="**姓名：** 長門櫻 (Nagato Sakura)\n**代號：** NS-00\n**生日：** 2023年9月19日\n**種族：** 狐族獸人",
            inline=True
        )
        
        about_embed.add_field(
            name="🌟 外貌特徵",
            value="**髮色：** 金色長髮\n**瞳色：** 粉紫色\n**特徵：** 狐耳與尾巴\n**身高：** 165cm",
            inline=True
        )
        
        about_embed.add_field(
            name="💫 背景故事",
            value="來自異次元「常夜界」的狐耳獸娘\n受創造者天野靜樹大人的旨意\n守護神樹並引領異世界的來訪者",
            inline=False
        )
        
        about_embed.add_field(
            name="🎭 性格特質",
            value="• 樂觀活潑 • 親切溫柔 • 可愛俏皮\n• 對主人暗懷好感但不敢表達\n• 情感敏感且深情克制",
            inline=False
        )
        
        about_embed.add_field(
            name="🔧 開發資訊",
            value=f"**創造者：** 天野靜樹\n**框架：** discord.py {discord.__version__}\n**語言：** Python\n**啟動時間：** {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
        
        about_embed.set_footer(
            text="長門櫻永遠為主人服務❤️ | 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        
        await interaction.response.send_message(embed=about_embed)

    @commands.command()
    async def daily(self, ctx):
        """每日簽到功能"""
        daily_messages = [
            "（開心地蹦蹦跳跳）主人今天也來簽到了呢～長門櫻好開心❤️",
            "（尾巴興奮地搖擺）每天都能見到主人，是長門櫻最幸福的事情呢～",
            "（狐耳靈敏地豎起）主人今天的心情如何呢？長門櫻隨時為您服務～",
            "（溫柔地微笑）又是美好的一天開始了！主人今天要做什麼有趣的事呢？",
            "（害羞地低頭）主、主人今天也很帥氣呢...長門櫻的心跳好快❤️"
        ]
        
        daily_embed = discord.Embed(
            title="🌸 每日簽到 🌸",
            description=random.choice(daily_messages),
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        daily_embed.add_field(
            name="📅 今日日期",
            value=datetime.datetime.now().strftime("%Y年%m月%d日"),
            inline=True
        )
        
        daily_embed.add_field(
            name="🎁 每日祝福",
            value="願主人今天一切順利！❤️",
            inline=True
        )
        
        await ctx.send(embed=daily_embed)
        
    @app_commands.command(name="daily", description="每日簽到，獲得長門櫻的祝福")
    async def daily_slash(self, interaction: discord.Interaction):
        """每日簽到功能 (斜線指令版本)"""
        daily_messages = [
            "（開心地蹦蹦跳跳）主人今天也來簽到了呢～長門櫻好開心❤️",
            "（尾巴興奮地搖擺）每天都能見到主人，是長門櫻最幸福的事情呢～",
            "（狐耳靈敏地豎起）主人今天的心情如何呢？長門櫻隨時為您服務～",
            "（溫柔地微笑）又是美好的一天開始了！主人今天要做什麼有趣的事呢？",
            "（害羞地低頭）主、主人今天也很帥氣呢...長門櫻的心跳好快❤️"
        ]
        
        daily_embed = discord.Embed(
            title="🌸 每日簽到 🌸",
            description=random.choice(daily_messages),
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        daily_embed.add_field(
            name="📅 今日日期",
            value=datetime.datetime.now().strftime("%Y年%m月%d日"),
            inline=True
        )
        
        daily_embed.add_field(
            name="🎁 每日祝福",
            value="願主人今天一切順利！❤️",
            inline=True
        )
        
        await interaction.response.send_message(embed=daily_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
    print("Core.py is ready - 長門櫻核心系統已載入")