import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

import discord
from discord import app_commands
from discord.ext import commands
import datetime

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_help_embed(self, ctx, interaction=None):
        # 創建主要幫助嵌入訊息
        help_embed = discord.Embed(
            title="🌸 長門櫻服務指南 🌸",
            description="（輕輕行禮）主人～這裡是長門櫻為您準備的完整服務列表❤️\n受天野靜樹大人之命，長門櫻會盡心為主人服務的～",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        help_embed.set_thumbnail(url=self.bot.user.avatar)

        # 基礎功能
        help_embed.add_field(
            name="🏠 **基礎功能**",
            value="`!DM` - 開啟與長門櫻的私人聊天\n`!Level [用戶]` - 查看等級資料卡\n`!Version` - 查看長門櫻版本資訊",
            inline=True
        )
        
        # 娛樂功能
        help_embed.add_field(
            name="🎮 **娛樂遊戲**",
            value="`!GuessingGameStart` - 猜數字遊戲\n`!SnakeGame` - 貪吃蛇遊戲\n`!Dice [面數] [次數]` - 擲骰子\n`!Choices [次數] [選項...]` - 隨機選擇\n`!Tarot` - 抽塔羅牌",
            inline=True
        )
        
        # 實用工具
        help_embed.add_field(
            name="🛠️ **實用工具**",
            value="`!Math [公式]` - 數學計算\n`!PrimeNumber [數字]` - 質數判斷\n`!Weather [縣市]` - 天氣查詢\n`!Translate [內容]` - 翻譯功能",
            inline=True
        )
        
        # 圖像處理
        help_embed.add_field(
            name="🎨 **圖像處理**",
            value="`!Sharpen [強度] + 圖片` - 銳化\n`!Blur [強度] + 圖片` - 模糊\n`!Brightness [亮度] + 圖片` - 亮度調整\n`!Mosaic [強度] + 圖片` - 馬賽克效果\n`!SuperDeformed` - 長門櫻Q版圖片",
            inline=True
        )
        
        # 音頻處理
        help_embed.add_field(
            name="🎵 **音頻功能**",
            value="`!AudioInfo + 音檔` - 音樂資訊分析\n`!AudioReverse + 音檔` - 反轉音頻\n`!AudioSpeed [倍速] + 音檔` - 調整速度\n`!Join/Leave` - 語音頻道控制\n`!Play [網址]` - 播放音樂",
            inline=True
        )
        
        # 智能功能
        help_embed.add_field(
            name="🤖 **AI智能功能**",
            value="`!CheckSMS [簡訊]` - 簡訊安全檢測\n`!FacialFeaturesDetection + 圖片` - 五官檢測\n`!GenerateQRCode [內容]` - QR碼生成",
            inline=True
        )
        
        # 自定義功能
        help_embed.add_field(
            name="⚙️ **自定義功能**",
            value="`!Add [指令] [內容]` - 新增指令\n`!Edit [指令] [內容]` - 編輯指令\n`!Remove [指令]` - 刪除指令\n`!VoteCreate [問題] [選項...]` - 創建投票",
            inline=False
        )
        
        # 特殊功能提示
        help_embed.add_field(
            name="✨ **特殊提示**",
            value="• 使用 `!FestivalEvent` 查看節日彩蛋\n• 大部分指令都支援 `/` 斜線指令格式\n• 附檔功能需要上傳對應的檔案類型\n• 長門櫻會根據您的互動獲得經驗值喔～",
            inline=False
        )
        
        help_embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者 | 輸入指令時記得加上驚嘆號 ！", 
            icon_url=self.bot.user.avatar
        )
        help_embed.timestamp = datetime.datetime.now()

        if ctx:
            await ctx.send(embed=help_embed)
        elif interaction:
            await interaction.response.send_message(embed=help_embed)

    @commands.command()
    async def Help(self, ctx):
        await self.send_help_embed(ctx)

    @app_commands.command(name="help", description="!Help - 顯示此幫助訊息")
    async def help(self, interaction: discord.Interaction):
        await self.send_help_embed(None, interaction)
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
    print("Help.py is ready")
