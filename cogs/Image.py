import discord
from discord.ext import commands
from PIL import Image as PILImage, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import io

class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['sharpen', 'SHARPEN'])
    async def Sharpen(self, ctx, strength: int = 25):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Sharpen指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            strength = max(1, min(100, strength))
            sharpen_factor = 0.1 + (2.0 * strength / 100.0)
            output = img.filter(ImageFilter.UnsharpMask(radius=int(2), percent=int(sharpen_factor * 100), threshold=1))
            output_bytes = io.BytesIO()
            output.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已將圖片銳化{strength}%")
            await ctx.send(file=discord.File(output_bytes, filename='sharpened_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Sharpen指令時調整銳化程度的正確方法為!Sharpen [1~100的整數]。")

    @commands.command(aliases=['blur', 'BLUR'])
    async def Blur(self, ctx, strength: int = 25):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Blur指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            strength = max(1, min(100, strength))
            blur_factor = 1.0 + (strength / 100.0)
            output = img.filter(ImageFilter.GaussianBlur(radius=blur_factor))
            output_bytes = io.BytesIO()
            output.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已將圖片模糊{strength}%")
            await ctx.send(file=discord.File(output_bytes, filename='blurred_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Blur指令時調整模糊程度的正確方法為!Blur [1~100的整數]。")

    @commands.command(aliases=['mosaic', 'MOSAIC'])
    async def Mosaic(self, ctx, size: int = 25):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Mosaic指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            size = max(1, min(100, size))
            output = img.resize((img.width // size, img.height // size), PILImage.NEAREST)
            output = output.resize((img.width, img.height), PILImage.NEAREST)
            output_bytes = io.BytesIO()
            output.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已將圖片套上馬賽克效果（大小：{size}）")
            await ctx.send(file=discord.File(output_bytes, filename='mosaic_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Mosaic指令時調整馬賽克大小的正確方法為!Mosaic [1~100的整數]。")

    @commands.command(aliases=['brightness', 'BRIGHTNESS'])
    async def Brightness(self, ctx, level: int = 50):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Brightness指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            level = max(0, min(100, level))
            enhancer = ImageEnhance.Brightness(img)
            output = enhancer.enhance(level / 50.0)
            output_bytes = io.BytesIO()
            output.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已調整圖片亮度（範圍：0~100，原始值：50）")
            await ctx.send(file=discord.File(output_bytes, filename='brightness_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Brightness指令時調整亮度的正確方法為!Brightness [0~100的整數]。")

    @commands.command(aliases=['contrast', 'CONTRAST'])
    async def Contrast(self, ctx, level: int = 50):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Contrast指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            level = max(0, min(100, level))
            enhancer = ImageEnhance.Contrast(img)
            output = enhancer.enhance(level / 50.0)
            output_bytes = io.BytesIO()
            output.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已調整圖片對比度（範圍：0~100，原始值：50）")
            await ctx.send(file=discord.File(output_bytes, filename='contrast_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Contrast指令時調整對比度的正確方法為!Contrast [0~100的整數]。")

    @commands.command(aliases=['color', 'COLOR'])
    async def Color(self, ctx, level: int = 50):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Color指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            level = max(0, min(100, level))
            enhancer = ImageEnhance.Color(img)
            output = enhancer.enhance(level / 50.0)
            output_bytes = io.BytesIO()
            output.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已調整圖片飽和度（範圍：0~100，原始值：50）")
            await ctx.send(file=discord.File(output_bytes, filename='color_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Color指令時調整飽和度的正確方法為!Color [0~100的整數]。")

    @commands.command(aliases=['icon', 'ICON'])
    async def Icon(self, ctx, opacity: int = 70):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!Icon指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            opacity = max(0, min(100, opacity))
            watermark = PILImage.open("assets/icon/1.5.μ.png").convert("RGBA")
            watermark = watermark.resize((128, 128))
            watermark.putalpha(int(255 * (opacity / 100.0)))
            position = (img.width - watermark.width, img.height - watermark.height)
            img.paste(watermark, position, watermark)
            output_bytes = io.BytesIO()
            img.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send(f"長門櫻已將圖片加上浮水印（透明度：{opacity}）")
            await ctx.send(file=discord.File(output_bytes, filename='watermarked_image.png'))

        except commands.BadArgument:
            await ctx.send("主人~使用!Icon指令時調整透明度的正確方法為!Icon [0~100的整數]。")



    @Sharpen.error
    async def sharpen_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Sharpen指令時調整銳化程度的正確方法為!Sharpen [1~100的整數]。")

    @Blur.error
    async def blur_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Blur指令時調整模糊程度的正確方法為!Blur [1~100的整數]。")

    @Mosaic.error
    async def mosaic_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Mosaic指令時調整馬賽克大小的正確方法為!Mosaic [1~100的整數]。")

    @Brightness.error
    async def brightness_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Brightness指令時調整亮度的正確方法為!Brightness [0~100的整數]。")

    @Contrast.error
    async def contrast_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Contrast指令時調整對比度的正確方法為!Contrast [0~100的整數]。")

    @Color.error
    async def color_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Color指令時調整飽和度的正確方法為!Color [0~100的整數]。")

    @Icon.error
    async def icon_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!Icon指令時調整透明度的正確方法為!Icon [1~100的整數]。")

async def setup(bot):
    await bot.add_cog(Image(bot))
    print("Image.py is ready")
