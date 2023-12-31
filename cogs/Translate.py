import discord
from discord.ext import commands
import googletrans

class Translate(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.translator = googletrans.Translator()

  @commands.command(aliases=["TS","translate"])
  async def Translate(self, ctx, *, text: str):
    try:
      text_language = self.translator.detect(text)
      if text_language.lang in ['zh-tw', 'zh-CN']:
        language = 'en'
        text_2 = self.translator.translate(text, dest=language).text
        await ctx.reply(f"{text_language.lang} -> {language}\n\n翻譯結果:\n{text_2}")
        
      elif text_language.lang == 'en':
        language_2 = 'zh-tw'
        text_2 = self.translator.translate(text, dest=language_2).text
        await ctx.reply(f"{text_language.lang} -> {language_2}\n\n翻譯結果:\n{text_2}")
        
      else:
        await ctx.reply('不支援的語言呢，請使用中文或英文哦~❤ 不好意思，其他語言我暫時無法理解呢！有其他需要我協助的事情嗎？（^^） ❤\n')
        return

    except Exception as e:
      await ctx.reply("翻譯時發生錯誤 >.< 有其他我可以幫忙的事情嗎？（^^）❤：" + str(e))
      
  @commands.command(aliases=["TST","translateto"])
  async def TranslateTo(self, ctx, target_language: str, *, text: str):
    await self.translate_and_send(ctx, text, target_language)

  async def translate_and_send(self, ctx, text, target_language):
    try:
      text_language = self.translator.detect(text)
      if target_language:
        text_language_2 = target_language.lower()
        if text_language_2 in googletrans.LANGUAGES:
          text_2 = self.translator.translate(text, dest=text_language_2).text
          await ctx.reply(f"{text_language.lang} -> {text_language_2}:\n\n翻譯結果:\n{text_2}")
        else:
          await ctx.reply("不支援的語言呢，請確保目標語言代碼正確哦~❤")
      else:
        await ctx.reply("請提供目標語言代碼，正確的格式是：!TranslateTo [語系] [翻譯內容] 喔~❤")
        return
      
    except Exception as e:
      await ctx.send("翻譯時發生錯誤 >.< 有其他我可以幫忙的事情嗎？（^^）❤：" + str(e))
    
  @commands.command(aliases=["TSH","translatehelp"]) 
  async def TranslateHelp(self,ctx):
    await ctx.reply('翻譯支援以下語系的互轉翻譯:\n' + str(googletrans.LANGUAGES) + '\n')
      
  @Translate.error
  async def Translate_error(self,ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.reply("請輸入您想要翻譯的文字，正確的格式是：!Translate [翻譯內容] 喔~❤") 
      
  @TranslateTo.error
  async def TranslateTo_error(self,ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.reply("請輸入您想要翻譯的文字，正確的格式是：!TranslateTo [語系] [翻譯內容] 喔~❤") 

async def setup(bot):
  await bot.add_cog(Translate(bot))
  print("Translate.py is ready")