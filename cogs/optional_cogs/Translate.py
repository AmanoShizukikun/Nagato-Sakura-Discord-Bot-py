import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import googletrans

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = googletrans.Translator()

    async def translate_text(self, ctx_or_interaction, text, target_language=None):
        try:
            text_language = self.translator.detect(text)
            target_language = target_language.lower() if target_language else None
        
            if target_language and target_language in googletrans.LANGUAGES:
                translated_text = self.translator.translate(text, dest=target_language).text
                if isinstance(ctx_or_interaction, commands.Context):
                    await ctx_or_interaction.reply(f"{text_language.lang} -> {target_language}:\n\n翻譯結果:\n{translated_text}")
                elif isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.response.send_message(f"{text_language.lang} -> {target_language}:\n\n翻譯結果:\n{translated_text}")
            else:
                if isinstance(ctx_or_interaction, commands.Context):
                    await ctx_or_interaction.reply("不支援的語言呢，請確保目標語言代碼正確哦~❤" if target_language else "請提供目標語言代碼，正確的格式是：!TranslateTo [語系] [翻譯內容] 喔~❤")
                elif isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.response.send_message("不支援的語言呢，請確保目標語言代碼正確哦~❤" if target_language else "請提供目標語言代碼，正確的格式是：!TranslateTo [語系] [翻譯內容] 喔~❤")
    
        except Exception as e:
            error_message = "翻譯時發生錯誤 >.< 有其他我可以幫忙的事情嗎？（^^）❤：" + str(e)
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(error_message)
            elif isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(error_message)

    @commands.command(aliases=["TS","translate"])
    async def Translate(self, ctx, *, text: str):
        try:
            text_language = self.translator.detect(text)
        
            if text_language.lang in ['zh-tw', 'zh-CN']:
                target_language = 'en'
            elif text_language.lang == 'en':
                target_language = 'zh-tw'
            else:
                await ctx.reply('不支援的語言呢，請使用中文或英文哦~❤ 不好意思，其他語言我暫時無法理解呢！有其他需要我協助的事情嗎？（^^） ❤\n')
                return
        
            translated_text = self.translator.translate(text, dest=target_language).text
            await ctx.reply(f"{text_language.lang} -> {target_language}\n\n翻譯結果:\n{translated_text}")
        
        except Exception as e:
            await ctx.reply("翻譯時發生錯誤 >.< 有其他我可以幫忙的事情嗎？（^^）❤：" + str(e))

    @commands.command(aliases=["TST","translateto"])
    async def TranslateTo(self, ctx, target_language: str, *, text: str):
        await self.translate_text(ctx, text, target_language)

    @commands.command(aliases=["TSH","translatehelp"]) 
    async def TranslateHelp(self, ctx):
        await ctx.reply('翻譯支援以下語系的互轉翻譯:\n' + str(googletrans.LANGUAGES) + '\n')
      
    @Translate.error
    async def Translate_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("請輸入您想要翻譯的文字，正確的格式是：!Translate [翻譯內容] 喔~❤") 
      
    @TranslateTo.error
    async def translate_to_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if ctx.command.name == "Translate":
                await ctx.reply("請輸入您想要翻譯的文字，正確的格式是：!Translate [翻譯內容] 喔~❤")
            elif ctx.command.name == "TranslateTo":
                await ctx.reply("請輸入您想要翻譯的文字，正確的格式是：!TranslateTo [語系] [翻譯內容] 喔~❤")

    @app_commands.command(name="translate", description="!Translate [翻譯內容] - 自動中翻英，英翻中")
    async def translate(self, interaction: discord.Interaction, text: str):
        try:
            text_language = self.translator.detect(text)

            if text_language.lang in ['zh-tw', 'zh-CN']:
                target_language = 'en'
            elif text_language.lang == 'en':
                target_language = 'zh-tw'
            else:
                await interaction.response.send_message('不支援的語言呢，請使用中文或英文哦~❤ 不好意思，其他語言我暫時無法理解呢！有其他需要我協助的事情嗎？（^^） ❤\n')
                return

            translated_text = self.translator.translate(text, dest=target_language).text
            await interaction.response.send_message(f"{text_language.lang} -> {target_language}\n\n翻譯結果:\n{translated_text}")

        except Exception as e:
            await interaction.response.send_message("翻譯時發生錯誤 >.< 有其他我可以幫忙的事情嗎？（^^）❤：" + str(e))
            
    @app_commands.command(name="translateto", description="!TranslateTo [語系] [翻譯內容] - 將翻譯內容翻譯成所選語系")
    async def translateto(self, interaction: discord.Interaction, target_language: str, text: str):
        await self.translate_text(interaction, text, target_language)

    @app_commands.command(name="translatehelp", description="!TranslateHelp - 顯示可翻譯語系")
    async def translatehelp(self, interaction: discord.Interaction):
        await interaction.response.send_message('翻譯支援以下語系的互轉翻譯:\n' + str(googletrans.LANGUAGES) + '\n')

async def setup(bot: commands.Bot):
    await bot.add_cog(Translate(bot))
    print("Translate.py is ready")