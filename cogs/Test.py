import discord
from discord.ext import commands
from discord.ui import Button, View

class Test(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.view = View(timeout=None)

  @commands.command()
  async def Test(self, ctx):
    if self.view is not None:                        #避免按鈕無限增加
      self.view.clear_items()
    else:
      self.view = View(timeout=None)
      
    button = Button(label="Test", style=discord.ButtonStyle.blurple)
    button.callback = self.button_callback
    self.view.add_item(button)
    await ctx.send("已添加按鈕，請查看消息", view=self.view)
    
  async def button_callback(self,interaction: discord.Interaction):
      await interaction.response.send_message("Hello")
        
async def setup(bot):
  await bot.add_cog(Test(bot))
  print("Test.py is ready")