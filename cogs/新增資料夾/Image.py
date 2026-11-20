import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image as PILImage, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import io
import dlib
import os
import numpy as np
import cv2
import random

class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.line_width = 6
        shape_predictor_path = os.path.join("data", "Image", "shape_predictor_68_face_landmarks.dat")
        eye_cascade_path = os.path.join("data", "Image", "haarcascade_eye.xml")
        mouth_cascade_path = os.path.join("data", "Image", "haarcascade_mcs_mouth.xml")
        nose_cascade_path = os.path.join("data", "Image", "haarcascade_mcs_nose.xml")
        for file_path in [shape_predictor_path, eye_cascade_path, mouth_cascade_path, nose_cascade_path]:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"The file {file_path} was not found.")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(shape_predictor_path)
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        self.mouth_cascade = cv2.CascadeClassifier(mouth_cascade_path)
        self.nose_cascade = cv2.CascadeClassifier(nose_cascade_path)

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
            watermark = PILImage.open("assets/icon/1.5.ν.png").convert("RGBA")
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
            
    @commands.command(aliases=['facialfeaturesdetection', 'FACIALFEATURESDETECTION'])
    async def FacialFeaturesDetection(self, ctx, line_width: int = None):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!FacialFeaturesDetection指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            img_np = np.array(img)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            faces = self.detector(gray)
            if len(faces) > 0:
                landmarks = self.predictor(gray, faces[0])
                draw = ImageDraw.Draw(img)
                line_width = line_width or self.line_width
                for i in range(36, 48):  # 36-47 is for the mouth
                    draw.line([tuple([landmarks.part(i).x, landmarks.part(i).y]), 
                               tuple([landmarks.part((i + 1) % 48).x, landmarks.part((i + 1) % 48).y])], 
                              fill=(255, 0, 0), width=line_width)

                for i in range(17, 27):  # 17-26 is for the nose
                    draw.line([tuple([landmarks.part(i).x, landmarks.part(i).y]), 
                               tuple([landmarks.part((i + 1) % 27).x, landmarks.part((i + 1) % 27).y])], 
                              fill=(0, 255, 0), width=line_width)

                for i in range(42, 60):  # 42-59 is for the eyes
                    draw.line([tuple([landmarks.part(i).x, landmarks.part(i).y]), 
                               tuple([landmarks.part((i + 1) % 60).x, landmarks.part((i + 1) % 60).y])], 
                              fill=(0, 0, 255), width=line_width)

                output_bytes = io.BytesIO()
                img.save(output_bytes, format='PNG')
                output_bytes.seek(0)

                await ctx.send("長門櫻已完成五官偵測並標記")
                await ctx.send(file=discord.File(output_bytes, filename='facial_features_detection.png'))
            else:
                await ctx.send("主人~找不到圖片中的臉部")

        except Exception as e:
            print(e)
            await ctx.send("主人~發生了一點錯誤，請稍後再試。")

    @commands.command(aliases=['facialfeaturesdetectmultiscale', 'FACIALFEATURESDETECTMULTISCALE'])
    async def FacialFeaturesDetectMultiScale(self, ctx, line_width: int = None):
        if not ctx.message.attachments:
            await ctx.send("主人~使用!FacialFeaturesDetectMultiScale指令時請記得附上圖片")
            return

        try:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            img = PILImage.open(io.BytesIO(image_bytes))
            img_np = np.array(img)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray)
            for (x, y, w, h) in eyes:
                cv2.rectangle(img_np, (x, y), (x+w, y+h), (0, 255, 0), 2)

            mouths = self.mouth_cascade.detectMultiScale(gray)
            for (x, y, w, h) in mouths:
                cv2.rectangle(img_np, (x, y), (x+w, y+h), (0, 0, 255), 2)

            noses = self.nose_cascade.detectMultiScale(gray)
            for (x, y, w, h) in noses:
                cv2.rectangle(img_np, (x, y), (x+w, y+h), (255, 0, 0), 2)

            img_with_boxes = PILImage.fromarray(img_np)
            line_width = line_width or self.line_width
            draw = ImageDraw.Draw(img_with_boxes)
            for (x, y, w, h) in eyes:
                draw.rectangle([x, y, x+w, y+h], outline=(0, 255, 0), width=line_width)

            for (x, y, w, h) in mouths:
                draw.rectangle([x, y, x+w, y+h], outline=(0, 0, 255), width=line_width)

            for (x, y, w, h) in noses:
                draw.rectangle([x, y, x+w, y+h], outline=(255, 0, 0), width=line_width)

            output_bytes = io.BytesIO()
            img_with_boxes.save(output_bytes, format='PNG')
            output_bytes.seek(0)
            await ctx.send("長門櫻已完成多尺度五官偵測並標記(眼睛綠色方框、嘴巴紅色方框、鼻子藍色方框)")
            await ctx.send(file=discord.File(output_bytes, filename='facial_features_detect_multiscale.png'))

        except Exception as e:
            print(e)
            await ctx.send("主人~發生了一點錯誤，請稍後再試。")
            
    @commands.command(aliases=["superdeformed","SD","ChibiCharacter","chibicharacter","Chibi","chibi"])
    async def SuperDeformed(self, ctx):
        superdeformed_folder = os.path.abspath(f'./assets/sticker/')
        if os.path.exists(superdeformed_folder):
            superdeformed_images = [f for f in os.listdir(superdeformed_folder) if f.endswith('.jpg') or f.endswith('.png')]
            if superdeformed_images:
                image_name = random.choice(superdeformed_images)
                image_path = os.path.join(superdeformed_folder, image_name)
                with open(image_path, 'rb') as f:
                    picture = discord.File(f)
                await ctx.send(file=picture)
            else:
                await ctx.send(f"抱歉啊~主人!長門櫻找不到貼圖。")
        else:
            await ctx.send(f"抱歉啊~主人!長門櫻找不到貼圖的資料夾。")
            
    @app_commands.command(name="superdeformed", description="!SuperDeformed - 顯示長門櫻的SDCG")
    async def superdeformed(self, interaction: discord.Integration):
        superdeformed_folder = os.path.abspath(f'./assets/sticker/')
        if os.path.exists(superdeformed_folder):
            superdeformed_images = [f for f in os.listdir(superdeformed_folder) if f.endswith('.jpg') or f.endswith('.png') or f.endswith('.jpeg')]
            if superdeformed_images:
                image_name = random.choice(superdeformed_images)
                image_path = os.path.join(superdeformed_folder, image_name)
                with open(image_path, 'rb') as f:
                    picture = discord.File(f)
                await interaction.response.send_message(file=picture)
            else:
                await interaction.response.send_message(f"抱歉啊~主人!長門櫻找不到貼圖。")
        else:
            await interaction.response.send_message(f"抱歉啊~主人!長門櫻找不到貼圖的資料夾。")

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
    
    @FacialFeaturesDetection.error
    async def facial_features_detection_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!FacialFeaturesDetection指令時請記得附上圖片。")
            
    @FacialFeaturesDetectMultiScale.error
    async def facial_features_detect_multiscale_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("主人~使用!FacialFeaturesDetectMultiScale指令時請記得附上圖片。")

async def setup(bot: commands.Bot):
    await bot.add_cog(Image(bot))
    print("Image.py is ready")
