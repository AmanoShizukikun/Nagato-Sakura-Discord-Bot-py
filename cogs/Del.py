import discord
from discord.ext import commands

class Del(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command(aliases=["DEL","del"])
  @commands.has_permissions(manage_messages=True)
  async def Del(self,ctx,count:int):
    await ctx.channel.purge(limit=count)
    await ctx.send(f"嘿嘿{ctx.author.mention}~ {count} 條訊息已經被刪除啦(^^) ღ 有什麼其他的事情我可以幫助您的嗎？")      
        
  @Del.error
  async def Del_error(self,ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.reply("嗚嗚~對不起，這好像是一個小小的錯誤呢，缺少了必需的參數 >.< 正確的格式應該是：「!Del [數字]」 這樣就沒問題啦！❤") 
    
async def setup(bot):
  await bot.add_cog(Del(bot))
  print("Del.py is ready")