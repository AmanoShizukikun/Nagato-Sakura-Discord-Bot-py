import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_help_embed(self, ctx, interaction=None):
        help_embed = discord.Embed(
            title="這是長門櫻 提供的服務喔~❤",
            description="關於我~的~全~部~❤(^^) ",
            color=discord.Color.random()
        )
        help_embed.set_thumbnail(url=self.bot.user.avatar)

        fields = [
            ("Audio", "!AudioInfo 附上聲音檔 - 查看音樂資訊並顯示波型 \n !AudioReverse 附上聲音檔 - 反轉聲音檔 \n !AudioSpeed [倍速] 附上聲音檔 - 調整聲音速度 \n !AudioBit [位元] 附上聲音檔 - 調整聲音位元"),
            ("CheckSMS", "!CheckSMS [文字] - 自製小型AI模型判斷簡訊的類別、簡訊中的電話、簡訊中的網址並且能檢測網址的安全性"),
            ("Choices", "!Choices [選擇次數] [選項0] [選項1] - 隨機抽取選擇次數的選項"),
            ("CustomCommands", "!Add [指令名稱] [指令內容] - 新增自訂指令 \n !Edit [指令名稱] [新的指令內容] - 編輯自訂指令 \n !Remove [指令名稱] - 刪除自訂指令"),
            ("Dice", "!Dice [骰子面數] [擲骰次數] - 擲骰子"),
            ("DM", "!DM - 邀請長門櫻私訊"),
            ("FestivalEvent", "!FestivalEvent - 當特殊的日子來臨之時會有彩蛋"),
            ("Game", "!GuessingGameStart - 開啟猜數字遊戲 \n !Guess [數字] - 猜數字 \n !SnakeGame - 玩貪吃蛇遊戲 \n !SnakeGameReset - 重置貪吃蛇遊戲"),
            ("GenerateCode", "!GenerateBarCode [12位數字] - 生成EAN13條碼 \n !GenerateQRCode [內容] [數字] - 生成QRCode"),
            ("Image", "!Sharpen [1~100的整數] 附上圖片 - 調整銳化程度 \n !Blur [1~100的整數] 附上圖片 - 調整模糊程度 \n !Mosaic [整數] 附上圖片 - 套上馬賽克效果 \n !Brightness [0~100的整數] 附上圖片 - 調整亮度 \n !Contrast [0~100的整數] 附上圖片 - 調整對比度 \n !Color [0~100的整數] 附上圖片 - 調整飽和度 \n !Icon [透明度(0~100的整數)] 附上圖片 - 添加浮水印 \n !FacialFeaturesDetection 附上圖片 - 五官偵測標記 \n !FacialFeaturesDetectMultiScale 附上圖片 - 五官偵測並標記(眼睛綠色方框、嘴巴紅色方框、鼻子藍色方框) \n !SuperDeformed - 可以隨機抽取長門櫻的Q版圖片"),
            ("Level", "!Level - 顯示個人資料卡"),
            ("Math", "!Math [計算公式] - 長門櫻幫您計算數學 \n !PrimeNumber [整數] - 判斷是否為質數"),
            ("Ping", "!Ping - 長門櫻在Discord WebSocket協議的延遲 \n !PingIP [網址] - 查詢網站 IP"),
            ("Tarot", "!Tarot - 抽塔羅牌"),
            ("Translate", "!Translate [翻譯內容] - 自動中翻英，英翻中 \n !TranslateTo [語系] [翻譯內容] - 將翻譯內容翻譯成所選語系 \n !TranslateHelp - 顯示可翻譯語系"),
            ("Version", "!Version - 顯示出長門櫻當前版本"),
            ("Video", "!VideoToGif [附加影片檔] [寬] [高] [起始時間] [結束時間] [幀數] - 將影片生成Gif"),
            ("Vote", "!VoteCreate [問題] [選項1] [選項2] [選項N] - 創建投票 \n !Vote [問題] [選項名稱] - 投票 \n  !VoteResult [問題] - 顯示投票結果"),
            ("Weather", "!Weather - 顯示六都的天氣預報 \n !Weather [縣市名稱] - 顯示指定縣市天氣 \n !AllWeather - 顯示所有縣市的天氣預報"),
            ("Youtube", "!Join - 長門櫻進入語音聊天室 \n !Leave - 長門櫻離開語音聊天室 \n !Play [網址] - 長門櫻播放音樂(目前支援以下平台:Youtube) \n !List - 長門櫻顯示撥放清單 \n !Skip [數字] - 跳過 [數字] 首歌")
        ]

        for name, value in fields:
            help_embed.add_field(name=name, value=value, inline=False)

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
