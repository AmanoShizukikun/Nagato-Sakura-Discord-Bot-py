import discord
from discord.ext import commands, tasks 
import logging
import logging.handlers
from itertools import cycle
import os
import random
from dotenv import load_dotenv

# 從 .env 讀取金鑰（.env 不會上傳到 GitHub）
load_dotenv()

# 配置機器人的日誌
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024, 
    backupCount=5,
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
bot_status = cycle([
    "為主人服務中", 
    "常夜界守護者", 
    "!Help 查看指令",
    "與 {guilds} 個伺服器互動"
])

@tasks.loop(hours=1)  # 每小時更換一次狀態
async def change_status():
    status_text = next(bot_status)
    if "{guilds}" in status_text:
        status_text = status_text.format(guilds=len(bot.guilds))
    await bot.change_presence(activity=discord.Game(status_text))

# 定義事件處理程序
@bot.event
async def on_ready():
    bot.bot_name = "長門櫻" # 使用者自訂機器人名稱
    print(f'已成功登錄為 {bot.user} ({bot.bot_name})')
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
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise SystemExit("找不到 DISCORD_TOKEN：請把 .env.example 複製成 .env 並填入機器人 Token")
bot.run(token)