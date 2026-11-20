import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime

async def send_private_message(user: discord.User):
    # 不同時間的問候語
    current_time = datetime.datetime.now()
    if 5 <= current_time.hour < 12:
        greeting = "早安"
        time_emoji = "🌅"
    elif 12 <= current_time.hour < 18:
        greeting = "午安"
        time_emoji = "☀️"
    elif 18 <= current_time.hour < 22:
        greeting = "晚安"
        time_emoji = "🌆"
    else:
        greeting = "深夜好"
        time_emoji = "🌙"
    
    # 隨機的長門櫻個性化訊息
    sakura_messages = [
        "（狐耳輕輕晃動）呀～主人找長門櫻了呢❤️",
        "（尾巴開心地搖擺）能為主人服務是長門櫻最開心的事情了～",
        "（雙眼閃閃發光）主人今天過得怎麼樣呢？",
        "（輕輕歪頭）有什麼長門櫻可以幫助主人的嗎？",
        "（害羞地低頭）主、主人突然聯絡長門櫻...好開心❤️"
    ]
    
    random_message = random.choice(sakura_messages)
    
    embed = discord.Embed(
        title=f"{time_emoji} {greeting}，主人～❤️",
        description=f"{random_message}\n\n✨ **歡迎來到長門櫻的私人空間** ✨",
        color=discord.Color.from_rgb(255, 182, 193)  # 粉色主題
    )
    
    embed.add_field(
        name="🌸 關於長門櫻",
        value="我是誕生於異次元常夜界的狐耳獸娘\n受到創造者天野靜樹的旨意來守護神樹\n並引領像主人這樣的異世界來訪者～",
        inline=False
    )
    
    embed.add_field(
        name="📋 快速指令",
        value="• `!Help` - 查看所有可用功能\n• `!Level` - 查看您的資料卡\n• `!Version` - 查看長門櫻的版本資訊\n• `!FestivalEvent` - 查看特殊節日彩蛋",
        inline=False
    )
    
    embed.add_field(
        name="💬 社群連結",
        value="**「三合音 TIM_ACG(長門櫻測試服)」**\n[加入測試服務器](https://discord.gg/sqS4TmFZxG)\n\n**「三合音 TIM_ACG」主服務器**\n[加入交流討論](https://discord.gg/YUKv7JFUpz)",
        inline=False
    )
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/your-channel/sakura-avatar.png")  # 可替換為長門櫻頭像
    embed.set_footer(text="長門櫻 • 常夜界神樹守護者", icon_url="https://cdn.discordapp.com/attachments/your-channel/sakura-icon.png")
    embed.timestamp = datetime.datetime.now()
    
    await user.send(embed=embed)

class DM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def DM(self, ctx):
        await send_private_message(ctx.author)

    @app_commands.command(name="dm", description="!DM - 邀請長門櫻私訊")
    async def dm(self, interaction: discord.Interaction):
        user = interaction.user
        await send_private_message(user)
        
        # 隨機回應訊息
        responses = [
            "（害羞地扭動尾巴）已、已經發送私訊給主人了...請查看喔❤️",
            "（興奮地豎起狐耳）長門櫻已經準備好與主人私聊了～",
            "（輕柔地微笑）私人訊息已送達，長門櫻在那裡等著主人呢❤️",
            "（開心地轉圈）呀～！長門櫻已經飛到主人的私訊裡了～",
            "（溫柔地點頭）主人的專屬私聊空間已經準備完畢了❤️"
        ]
        
        response_msg = random.choice(responses)
        
        embed = discord.Embed(
            title="🌸 私訊服務已開啟",
            description=response_msg,
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(DM(bot))
    print("DM.py is ready")