import discord
from discord import app_commands
from discord.ext import commands
import random

class Choices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["choices","CHOICES"])
    async def Choices(self, ctx, num_choices: int, *options):
        if len(options) < num_choices:
            await ctx.send("主人，提供的選項數量有點不夠呢，可以再多給我一些選項供隨機選擇嗎？")
            return
        selected_choices = random.sample(options, num_choices)
        selected_choices_text = "\n".join(selected_choices)
        await ctx.send(f"抽取的結果為...\n{selected_choices_text}")
        
    @Choices.error
    async def Math_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("請輸入您想要抽取的選項，正確的格式是：!Choices [選擇次數] [選項0] [選項1] ... 喔~❤") 
            
    @app_commands.command(name="choices", description="!Choices [選擇次數] [選項0] [選項1] - 隨機抽取選擇次數的選項")
    async def choices(self, interaction: discord.Interaction, num_choices: int, options: str):
        options_list = options.split()
        if len(options_list) < num_choices:
            await interaction.response.send_message("主人，提供的選項數量有點不夠呢，可以再多給我一些選項供隨機選擇嗎？")
            return
        selected_choices = random.sample(options_list, num_choices)
        selected_choices_text = "\n".join(selected_choices)
        await interaction.response.send_message(f"抽取的結果為...\n{selected_choices_text}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Choices(bot))
    print("Choices.py is ready")
