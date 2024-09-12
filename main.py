import discord
from discord.ext import commands, tasks 
import logging
import logging.handlers
import os
import random
from itertools import cycle

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
intents.guilds = True  

# 創建 commands.Bot 實例
bot = commands.Bot(command_prefix=["!", "！"],intents=discord.Intents.all())

# 機器人狀態
bot_status = cycle(["Your bot event"])
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
    slash = await bot.tree.sync()
    print(f"載入 {len(slash)} 個斜線指令")
    
# 載入指令程式檔案
@bot.command()
async def load(ctx: commands.Context, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} done.")

# 卸載指令檔案
@bot.command()
async def unload(ctx: commands.Context, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"UnLoaded {extension} done.")

# 重新載入程式檔案
@bot.command()
async def reload(ctx: commands.Context, extension):
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"ReLoaded {extension} done.")
    
async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                print(f"加載擴展失敗 {filename[:-3]}: {e}")
    print('------一般擴展加載完畢')
                
#運行機器人
bot.run('Your bot token')
