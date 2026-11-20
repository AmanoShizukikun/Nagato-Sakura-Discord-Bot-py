import discord
from discord import app_commands
from discord.ext import commands
import random

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["DICE","dice"])
    async def Dice(self, ctx, sides: int, rolls: int = 1):
        if sides < 2:
            await ctx.send("主人~骰子至少需要兩個面。")
            return

        if rolls < 1:
            await ctx.send("主人~擲骰次數至少為1次。")
            return

        results = [random.randint(1, sides) for _ in range(rolls)]

        if rolls == 1:
            await ctx.send(f"{ctx.author.mention} 擲出了：{results[0]}")
        else:
            result_str = ", ".join(map(str, results))
            await ctx.send(f"{ctx.author.mention} 擲出了：{result_str}")
            
    @app_commands.command(name="dice", description="!Dice [骰子面數] [擲骰次數] - 擲骰子")
    async def dice(self, interaction: discord.Interaction, sides: int, rolls: int = 1):
        if sides < 2:
            await interaction.response.send_message("主人~骰子至少需要兩個面。")
            return

        if rolls < 1:
            await interaction.response.send_message("主人~擲骰次數至少為1次。")
            return

        results = [random.randint(1, sides) for _ in range(rolls)]

        if rolls == 1:
            await interaction.response.send_message(f"{interaction.user.mention} 擲出了：{results[0]}")
        else:
            result_str = ", ".join(map(str, results))
            await interaction.response.send_message(f"{interaction.user.mention} 擲出了：{result_str}")
            
async def setup(bot: commands.Bot):
    await bot.add_cog(Dice(bot))
    print("Dice.py is ready")
