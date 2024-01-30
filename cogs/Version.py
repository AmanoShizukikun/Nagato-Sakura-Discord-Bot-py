import discord
from discord.ext import commands

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self,ctx):
        version = "1.5.ν"
        directory = 'assets/preview/'
        output_path = f"{directory}{version}.png"
        await ctx.send(f"# {version}")
        await ctx.send(file=discord.File(output_path))
        await ctx.send(f"### 重要變更 \n\n - 新增Audio.py、Image.py")
        await ctx.send(f"### 新增功能 \n\n - !AudioInfo 附上聲音檔 - 查看音樂資訊並顯示波型\n - !AudioReverse 附上聲音檔 - 反轉聲音檔\n - !AudioSpeed [倍速] 附上聲音檔 - 調整聲音速度\n - !AudioBit [位元] 附上聲音檔 - 調整聲音位元\n- !Sharpen [1~100的整數] 附上圖片 - 調整銳化程度\n- !Blur [1~100的整數] 附上圖片 - 調整模糊程度\n- !Mosaic [整數] 附上圖片 - 套上馬賽克效果\n- !Brightness [0~100的整數] 附上圖片 - 調整亮度\n- !Contrast [0~100的整數] 附上圖片 - 調整對比度\n- !Color [0~100的整數] 附上圖片 - 調整飽和度\n- !Icon [透明度(0~100的整數)] 附上圖片 - 添加浮水印")
        await ctx.send(f"### 已知問題 \n\n - N/A")
    
async def setup(bot):
    await bot.add_cog(Version(bot))
    print("Version.py is ready")