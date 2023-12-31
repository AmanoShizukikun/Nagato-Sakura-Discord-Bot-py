# 匯入必要的模組
import discord
from discord.ext import commands, tasks 
import logging
import logging.handlers
from itertools import cycle
import os
import random

# 配置機器人的日誌
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # 保留5個日誌檔案
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 定義機器人的意圖
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  #
# 創建 commands.Bot 實例
bot = commands.Bot(command_prefix="!",intents=discord.Intents.all())

# 機器人狀態
bot_status = cycle(["TIM_WIYW 的VS Code"])
@tasks.loop(hours=24)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(bot_status)))

# 定義事件處理程序
@bot.event
async def on_ready():
    print(f'已成功登錄為 {bot.user}')
    change_status.start()
    print('------正在加載擴展')
    await load()
    
async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                print(f"加載擴展失敗 {filename[:-3]}: {e}")
    print('------擴展加載完畢')
                
#運行機器人
bot.run('機器人的token')