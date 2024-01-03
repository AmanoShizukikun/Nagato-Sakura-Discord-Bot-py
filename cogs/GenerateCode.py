import discord
from discord.ext import commands
import os
from barcode import EAN13
from barcode.writer import ImageWriter
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import VerticalBarsDrawer,RoundedModuleDrawer,HorizontalBarsDrawer,SquareModuleDrawer,GappedSquareModuleDrawer,CircleModuleDrawer

class GenerateCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def create_directory(self):
        directory = 'data/GenerateCode/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory
    
    @commands.command(aliases=["GBC","generatebarcode","GENERATEBARCODE"])
    async def GenerateBarCode(self, ctx, number):
        try:
            directory = await self.create_directory()
            output = f"{directory}BarCode"
            Bar_code = EAN13(number, writer=ImageWriter())
            Bar_code.save(output)
            output_path = f"{directory}BarCode.png"
            await ctx.send(file=discord.File(output_path))
        except Exception as e:
            print(f"生成條碼時發生錯誤：{e}")
            await ctx.send("無法生成條碼請輸入12位數字")

    @commands.command(aliases=["GQRC","generateqrcode","GENERATEQRCODE"])
    async def GenerateQRCode(self, ctx, *args):
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        message = args[0] if args else ""
        version = 1

        if len(args) > 1 and args[1].isdigit():
            version = int(args[1])
            
            if version == 2:
                await self.generate_version_two(ctx, message)
                return
            
            elif version == 3:
                await self.generate_version_three(ctx, message)
                return
            
            elif version == 4:
                await self.generate_version_four(ctx, message)
                return
            
            elif version == 5:
                await self.generate_version_five(ctx, message)
                return
            
            elif version == 6:
                await self.generate_version_six(ctx, message)
                return
            
        has_image_attachment = any(attachment.content_type.startswith('image') for attachment in ctx.message.attachments)
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        if not has_image_attachment:
            try:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4
                )
                qr.add_data(message)
                qr.make(fit=True)
                QR_code = qr.make_image(image_factory=StyledPilImage, module_drawer=SquareModuleDrawer())
                QR_code.save(output_path)
                await ctx.send(file=discord.File(output_path))
            except Exception as e:
                print(f"生成QRCod時發生錯誤：{e}")
                await ctx.send("無法生成QRCod")
                return
        for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
                filename = f"{directory}{attachment.filename}"
                await attachment.save(filename)
                try:
                    qr = qrcode.QRCode(
                        version=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12,
                        border=4
                    )
                    qr.add_data(message)
                    qr.make(fit=True)
                    QR_code = qr.make_image(image_factory=StyledPilImage, embeded_image_path=filename)
                    QR_code.save(output_path)
                    await ctx.send(file=discord.File(output_path))
                except Exception as e:
                    print(f"生成QRCod時發生錯誤：{e}")
                    await ctx.send("無法生成QRCod")
    
    async def generate_version_two(self, ctx, message):
        has_image_attachment = any(attachment.content_type.startswith('image') for attachment in ctx.message.attachments)
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        if not has_image_attachment:
            try:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4
                )
                qr.add_data(message)
                qr.make(fit=True)
                QR_code = qr.make_image(image_factory=StyledPilImage, module_drawer=GappedSquareModuleDrawer())
                QR_code.save(output_path)
                await ctx.send(file=discord.File(output_path))
            except Exception as e:
                print(f"生成版本2的QRCod時發生錯誤：{e}")
                await ctx.send("無法生成版本2的QRCod")
        for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
                filename = f"{directory}{attachment.filename}"
                await attachment.save(filename)
                try:
                    qr = qrcode.QRCode(
                        version=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12,
                        border=4
                    )
                    qr.add_data(message)
                    qr.make(fit=True)
                    QR_code = qr.make_image(image_factory=StyledPilImage,module_drawer=GappedSquareModuleDrawer(), embeded_image_path=filename)
                    QR_code.save(output_path)
                    await ctx.send(file=discord.File(output_path))
                except Exception as e:
                    print(f"生成QRCod時發生錯誤：{e}")
                    await ctx.send("無法生成QRCod")
    
    async def generate_version_three(self, ctx, message):
        has_image_attachment = any(attachment.content_type.startswith('image') for attachment in ctx.message.attachments)
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        if not has_image_attachment:
            try:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4
                )
                qr.add_data(message)
                qr.make(fit=True)
                QR_code = qr.make_image(image_factory=StyledPilImage, module_drawer=CircleModuleDrawer())
                QR_code.save(output_path)
                await ctx.send(file=discord.File(output_path))
            except Exception as e:
                print(f"生成版本3的QRCod時發生錯誤：{e}")
                await ctx.send("無法生成版本3的QRCod")
        for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
                filename = f"{directory}{attachment.filename}"
                await attachment.save(filename)
                try:
                    qr = qrcode.QRCode(
                        version=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12,
                        border=4
                    )
                    qr.add_data(message)
                    qr.make(fit=True)
                    QR_code = qr.make_image(image_factory=StyledPilImage,module_drawer=CircleModuleDrawer(), embeded_image_path=filename)
                    QR_code.save(output_path)
                    await ctx.send(file=discord.File(output_path))
                except Exception as e:
                    print(f"生成QRCod時發生錯誤：{e}")
                    await ctx.send("無法生成QRCod")
    
    async def generate_version_four(self, ctx, message):
        has_image_attachment = any(attachment.content_type.startswith('image') for attachment in ctx.message.attachments)
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        if not has_image_attachment:
            try:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4
                )
                qr.add_data(message)
                qr.make(fit=True)
                QR_code = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
                QR_code.save(output_path)
                await ctx.send(file=discord.File(output_path))
            except Exception as e:
                print(f"生成版本4的QRCod時發生錯誤：{e}")
                await ctx.send("無法生成版本4的QRCod")
        for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
                filename = f"{directory}{attachment.filename}"
                await attachment.save(filename)
                try:
                    qr = qrcode.QRCode(
                        version=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12,
                        border=4
                    )
                    qr.add_data(message)
                    qr.make(fit=True)
                    QR_code = qr.make_image(image_factory=StyledPilImage,module_drawer=RoundedModuleDrawer(), embeded_image_path=filename)
                    QR_code.save(output_path)
                    await ctx.send(file=discord.File(output_path))
                except Exception as e:
                    print(f"生成QRCod時發生錯誤：{e}")
                    await ctx.send("無法生成QRCod")
    
    async def generate_version_five(self, ctx, message):
        has_image_attachment = any(attachment.content_type.startswith('image') for attachment in ctx.message.attachments)
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        if not has_image_attachment:
            try:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4
                )
                qr.add_data(message)
                qr.make(fit=True)
                QR_code = qr.make_image(image_factory=StyledPilImage, module_drawer=VerticalBarsDrawer())
                QR_code.save(output_path)
                await ctx.send(file=discord.File(output_path))
            except Exception as e:
                print(f"生成版本5的QRCod時發生錯誤：{e}")
                await ctx.send("無法生成版本5的QRCod")
        for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
                filename = f"{directory}{attachment.filename}"
                await attachment.save(filename)
                try:
                    qr = qrcode.QRCode(
                        version=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12,
                        border=4
                    )
                    qr.add_data(message)
                    qr.make(fit=True)
                    QR_code = qr.make_image(image_factory=StyledPilImage,module_drawer=VerticalBarsDrawer(), embeded_image_path=filename)
                    QR_code.save(output_path)
                    await ctx.send(file=discord.File(output_path))
                except Exception as e:
                    print(f"生成QRCod時發生錯誤：{e}")
                    await ctx.send("無法生成QRCod")
    
    async def generate_version_six(self, ctx, message):
        has_image_attachment = any(attachment.content_type.startswith('image') for attachment in ctx.message.attachments)
        directory = await self.create_directory()
        output_path = f"{directory}QRCode.png"
        if not has_image_attachment:
            try:
                qr = qrcode.QRCode(
                    version=3,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4
                )
                qr.add_data(message)
                qr.make(fit=True)
                QR_code = qr.make_image(image_factory=StyledPilImage, module_drawer=HorizontalBarsDrawer())
                QR_code.save(output_path)
                await ctx.send(file=discord.File(output_path))
            except Exception as e:
                print(f"生成版本6的QRCod時發生錯誤：{e}")
                await ctx.send("無法生成版本6的QRCod")
        for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
                filename = f"{directory}{attachment.filename}"
                await attachment.save(filename)
                try:
                    qr = qrcode.QRCode(
                        version=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=12,
                        border=4
                    )
                    qr.add_data(message)
                    qr.make(fit=True)
                    QR_code = qr.make_image(image_factory=StyledPilImage,module_drawer=HorizontalBarsDrawer(), embeded_image_path=filename)
                    QR_code.save(output_path)
                    await ctx.send(file=discord.File(output_path))
                except Exception as e:
                    print(f"生成QRCod時發生錯誤：{e}")
                    await ctx.send("無法生成QRCod")

async def setup(bot):
    await bot.add_cog(GenerateCode(bot))
    print("GenerateCode.py is ready")