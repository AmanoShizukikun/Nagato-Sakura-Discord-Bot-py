import discord
from discord.ext import commands
from numpy import *
import numexpr


class Math(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command(aliases=["calc","solve","math","MATH"])
  async def Math(self,ctx, *,expression:str):
    try:
      answer = numexpr.evaluate(expression)
      await ctx.reply(f"{expression} = {answer}") 
    except:
      await ctx.reply("噫~糟糕！出現了一個錯誤：「無效的表達式」 >.< 輸入 !MathHelp - 來顯示計算指令 (^^) ❤")   
      
  @commands.command(aliases=["MH","mathhelp","MATHHELP"])
  async def MathHelp(self,ctx):
    mathhelp_embed = discord.Embed(
      title="長門櫻 提供的計算服務喔~❤",
      description="關於計算的指令~❤(^^) ",
      color=discord.Color.random()
      )
    mathhelp_embed.set_thumbnail(url=ctx.bot.user.avatar)
    mathhelp_embed.add_field(name="where(bool, num1, num2)",value="如果布爾條件為 true，則為 num1，否則為 num2。",inline=False)
    mathhelp_embed.add_field(name="{sin,cos,tan}(float|complex)",value="三角正弦、餘弦或正切",inline=False)
    mathhelp_embed.add_field(name="{arcsin,arccos,arctan}(float|complex)",value="三角函數反正弦、餘弦或正切",inline=False)
    mathhelp_embed.add_field(name="arctan2(float1, float2)",value="float1/float2 的三角反正切",inline=False)
    mathhelp_embed.add_field(name="{sinh,cosh,tanh}(float|complex)",value="雙曲正弦、餘弦或正切",inline=False)
    mathhelp_embed.add_field(name="{arcsinh,arccosh,arctanh}(float|complex)",value="雙曲反正弦、餘弦或正切",inline=False)
    mathhelp_embed.add_field(name="{log,log10,log1p}(float|complex)",value="自然對數、以 10 為底的對數和 log(1+x) 對數",inline=False)
    mathhelp_embed.add_field(name="{exp,expm1}(float|complex)",value="指數和指數減一",inline=False)
    mathhelp_embed.add_field(name="sqrt(float|complex)",value="平方根",inline=False)
    mathhelp_embed.add_field(name="abs(float|complex)",value="絕對值",inline=False)
    mathhelp_embed.add_field(name="conj(complex)",value="共軛值",inline=False)
    mathhelp_embed.add_field(name="{real,imag}(complex)",value="複數的實部或虛部",inline=False)
    mathhelp_embed.add_field(name="complex(float, float)",value="由實部和虛部組成的複數",inline=False)
    mathhelp_embed.add_field(name="contains(np.str, np.str)",value="對於op1包含 的每個字符串返回 True op2",inline=False)
    await ctx.send(embed=mathhelp_embed)          
        
      
  @Math.error
  async def Math_error(self,ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.reply("請輸入您想要計算的公式(可以輸入指令 !MathHelp 查詢公式)，正確的格式是：!Math [計算的公式] 喔~❤") 
        
async def setup(bot):
  await bot.add_cog(Math(bot))
  print("Math.py is ready")