import discord
from discord.ext import commands
import math

class PrimeNumber(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["primenumber", "PRIMENUMBER"])
    async def PrimeNumber(self, ctx, num: int):
        if num < 2:
            await ctx.send(f"{num} 不是質數")
        elif num == 2:
            await ctx.send(f"{num} 是質數")
        elif num % 2 == 0:
            await ctx.send(f"{num} 不是質數")
        else:
            is_prime = True
            sqrt_num = int(math.sqrt(num))
            for i in range(3, sqrt_num + 1, 2):
                if num % i == 0:
                    is_prime = False
                    break
            if is_prime:
                await ctx.send(f"{num} 是質數")
            else:
                await ctx.send(f"{num} 不是質數")
            
async def setup(bot):
    await bot.add_cog(PrimeNumber(bot))
    print("PrimeNumber.py is ready")
    