import discord
from discord.ext import commands

class Ping(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command(aliases=["PING","ping"])
  async def Ping(self,ctx):
        bot_latency = round(self.bot.latency * 1000)
        await ctx.send(f"目前延遲為: {bot_latency} ms")     
        
async def setup(bot):
  await bot.add_cog(Ping(bot))
  print("Ping.py is ready")