import discord
from discord import app_commands
from discord.ext import commands

async def send_private_message(user: discord.User):
    message = (
        f"【 https://discord.gg/sqS4TmFZxG 】\n\n"
        f"★ 主人~❤ 這個是 **「三合音 TIM_ACG(長門櫻測試服)」** 寄來的邀請函\n"
        f"★ 誠摯的邀請您來加入測試開發的過程\n\n"
        f"▶ **加入「三合音 TIM_ACG」** 來和我們互相交流討論! https://discord.gg/YUKv7JFUpz \n\n"
        f"主人~❤ 感謝您開啟私聊服務 有什麼我可以為您效勞的嗎？\n"
        f"請輸入 `!Help` 讓我進一步協助您吧！^_^"
    )
    await user.send(message)

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
        await interaction.response.send_message(f"\n主人~❤ 已為您開啟私聊服務請前往私人訊息查看")

async def setup(bot: commands.Bot):
    await bot.add_cog(DM(bot))
    print("DM.py is ready")