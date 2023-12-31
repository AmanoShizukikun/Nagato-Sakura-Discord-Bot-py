import discord
from discord.ext import commands

class DM(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command()
  async def DM(self,ctx):
    await ctx.author.send(f"【 https://discord.gg/sqS4TmFZxG 】\n\n★ 主人~❤ 這個是 **「三合音 TIM_ACG(小妖精測試服)」** 寄來的邀請函\n★ 誠摯的邀請您來加入測試開發的過程\n\n▶ **加入「三合音 TIM_ACG」** 來和我們互相交流討論! https://discord.gg/YUKv7JFUpz ")
    await ctx.author.send(f"\n主人~❤ 感謝您開啟私聊服務 有什麼我可以為您效勞的嗎？\n請輸入 `!Help` 讓我進一步協助您吧！^_^")
        
async def setup(bot):
  await bot.add_cog(DM(bot))
  print("DM.py is ready")