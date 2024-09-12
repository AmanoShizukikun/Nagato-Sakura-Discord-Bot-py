import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

class WebCrawler(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command(aliases=["webcrawler","WEBCRAWLER"])
  async def WebCrawler(self,ctx, url: str , output_type: str = "title"): 
        try:
            res = requests.get(url)
            res.raise_for_status()  
            html = res.content.decode()
            soup = BeautifulSoup(html, 'html.parser')
            
            if output_type == "title":
                content = soup.title.string
            elif output_type == "text":
                content = soup.get_text()
            else:
                content = "不支持的輸出類別"

            await ctx.send(content)
        except requests.exceptions.RequestException as e:
            await ctx.send(f"發生錯誤：{e}")
        except Exception as e:
            await ctx.send(f"發生未知錯誤：{e}")
            
async def setup(bot):
  await bot.add_cog(WebCrawler(bot))
  print("WebCrawler.py is ready")