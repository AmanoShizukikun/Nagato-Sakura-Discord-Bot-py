import discord
from discord import app_commands
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
    
    @app_commands.command(name="del", description="!Del [數字] - 一次刪除大量訊息")
    @commands.has_permissions(manage_messages=True)
    async def delete_messages(self, interaction: discord.Interaction, count: int):
        await interaction.channel.purge(limit=count)
        await interaction.response.send_message(f"嘿嘿~ {count} 條訊息已經被刪除啦(^^) ღ 有什麼其他的事情我可以幫助您的嗎？") 
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Del(bot))
    print("Del.py is ready")