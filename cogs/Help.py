import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os

class Help(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.view = View(timeout=None)
        self.button_click_counts = {} 
    
    @commands.command()
    async def Help(self,ctx):
        if self.view is not None:
            self.view.clear_items()
        else:
            self.view = View(timeout=None)
      
        help_embed = discord.Embed(
            title="這是長門櫻 提供的幫助喔~❤",
            description="關於我~的~全~部~❤(^^) ",
            color=discord.Color.random()
            )
        help_embed.set_thumbnail(url=ctx.bot.user.avatar)
        help_embed.add_field(name="CheckSMS",value="!CheckSMS [文字] - 自製小型AI模型判斷簡訊類別",inline=False)
        help_embed.add_field(name="Choices",value="!Choices [選擇次數] [選項0] [選項1] - 隨機抽取選擇次數的選項",inline=False)
        help_embed.add_field(name="CustomCommands",value="!Add [指令名稱] [指令內容] - 新增自訂指令 \n !Edit [指令名稱] [新的指令內容] - 編輯自訂指令 \n !Remove [指令名稱] - 刪除自訂指令",inline=False)
        help_embed.add_field(name="Del",value="!Del [數字] - 一次刪除大量訊息",inline=False)
        help_embed.add_field(name="Dice",value="!Dice [骰子面數] [擲骰次數] - 擲骰子",inline=False)
        help_embed.add_field(name="DM",value="!DM - 邀請長門櫻私訊",inline=False)
        help_embed.add_field(name="GenerateCode",value="!GenerateBarCode [12位數字] - 生成EAN13條碼 \n !GenerateQRCode [內容] [數字] - 生成QRCode",inline=False)
        help_embed.add_field(name="Game",value="!GuessingGameStart - 開啟猜數字遊戲 \n !Guess [數字] - 猜數字",inline=False)
        help_embed.add_field(name="Level",value="!Level - 顯示個人資料卡",inline=False)
        help_embed.add_field(name="Math",value="!Math [計算公式] - 長門櫻幫您計算數學 \n !PrimeNumber [整數] - 判斷是否為質數",inline=False)
        help_embed.add_field(name="Ping",value="!Ping - 長門櫻在Discord WebSocket協議的延遲 \n !PingIP [網址] - 查詢網站 IP",inline=False)
        help_embed.add_field(name="Tarot",value="!Tarot - 抽塔羅牌",inline=False)
        help_embed.add_field(name="Translate",value="!Translate [翻譯內容] - 自動中翻英，英翻中 \n !TranslateTo [語系] [翻譯內容] - 將翻譯內容翻譯成所選語系 \n !TranslateHelp - 顯示可翻譯語系",inline=False)
        help_embed.add_field(name="Version",value="!Version - 顯示出長門櫻當前版本",inline=False)
        help_embed.add_field(name="Video",value="!VideoToGif [附加影片檔] [寬] [高] [起始時間] [結束時間] [幀數] - 將影片生成Gif",inline=False)
        help_embed.add_field(name="Vote",value="!VoteCreate [問題] [選項1] [選項2] [選項N] - 創建投票 \n !Vote [問題] [選項名稱] - 投票 \n  !VoteResult [問題] - 顯示投票結果",inline=False)
        help_embed.add_field(name="Weather",value="!Weather - 顯示六都的天氣預報 \n !Weather [縣市名稱] - 顯示指定縣市天氣 \n !AllWeather - 顯示所有縣市的天氣預報",inline=False)
        help_embed.add_field(name="Youtube",value="!Join - 長門櫻進入語音聊天室 \n !Leave - 長門櫻離開語音聊天室 \n !Play [網址] - 長門櫻播放音樂(目前支援以下平台:Youtube) \n !List - 長門櫻顯示撥放清單 \n !Skip [數字] - 跳過 [數字] 首歌",inline=False)
    
        yes_button = Button(label="是", style=discord.ButtonStyle.blurple)
        yes_button.callback = self.yes_button_callback
        self.view.add_item(yes_button)
    
        no_button = Button(label="否", style=discord.ButtonStyle.red)
        no_button.callback = self.no_button_callback
        self.view.add_item(no_button)
    
        await ctx.send(embed=help_embed)
        await ctx.send("這個回覆有幫助?",view=self.view )     
    
    async def yes_button_callback(self,interaction: discord.Interaction):
        await interaction.message.delete()
        guild_id = interaction.guild.id
        button_click_count = self.button_click_counts.get(guild_id, {"yes": 0, "no": 0})
        button_click_count["yes"] += 1
        self.button_click_counts[guild_id] = button_click_count
        self.save_button_click_counts("Help", guild_id)
        await interaction.response.send_message("已收到您的回覆")
  
    async def no_button_callback(self,interaction: discord.Interaction):
        await interaction.message.delete()
        guild_id = interaction.guild.id 
        button_click_count = self.button_click_counts.get(guild_id, {"yes": 0, "no": 0})
        button_click_count["no"] += 1
        self.button_click_counts[guild_id] = button_click_count
        self.save_button_click_counts("Help", guild_id)
        await interaction.response.send_message("已收到您的回覆")
    
    def save_button_click_counts(self, filename, guild_id):
        server_folder = f'./server/{guild_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"{filename}_{guild_id}.json")
        with open(file_name, "w") as file:
            json.dump(self.button_click_counts, file, indent=4)   
    
async def setup(bot):
    await bot.add_cog(Help(bot))
    print("Help.py is ready")
