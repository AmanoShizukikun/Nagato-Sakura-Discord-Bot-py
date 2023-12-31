import discord
from discord.ext import commands

class Userinfo(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=["userinfo","USERINFO"])
  async def Userinfo(self, ctx, member: discord.Member=None):
    if member is None:
      member = ctx.author
    elif member is not None:
      member = member
      
    info_embed = discord.Embed(title=f"{member.name}用戶資訊",description="用戶的所有資訊" ,color=member.color)
    info_embed.set_thumbnail(url=member.avatar)
    info_embed.add_field(name="用戶名稱", value=member.name, inline=False)
    info_embed.add_field(name="用戶暱稱", value=member.display_name, inline=False)
    info_embed.add_field(name="用戶驗證", value=member.discriminator, inline=False)
    info_embed.add_field(name="用戶 ID", value=member.id, inline=False)
    info_embed.add_field(name="用戶身分", value=member.top_role, inline=False)
    info_embed.add_field(name="用戶狀態", value=member.status, inline=False)
    info_embed.add_field(name="機器人?", value=member.bot, inline=False)
    info_embed.add_field(name="帳戶建立日期", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    info_embed.add_field(name="加入伺服器日期", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    
    await ctx.reply(embed=info_embed) 

async def setup(bot):
  await bot.add_cog(Userinfo(bot))
  print("Userinfo.py is ready")