import discord
from discord.ext import commands
import random
import os
import json
from PIL import Image

class Tarot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["tarot","TAROT"])
    async def Tarot(self, ctx):
        tarot_folder = os.path.abspath('./data/Tarot/')
        os.makedirs(tarot_folder, exist_ok=True)

        tarot_file = os.path.abspath('./data/Tarot/Tarot.json')
        with open(tarot_file, "r", encoding="utf-8") as file:
            tarot_data = json.load(file)

        tarot_number = random.randint(0, 21)
        is_reverse = random.choice([True, False])  

        image_filename = os.path.join(tarot_folder, f"{tarot_number}.png")

        try:
            with open(image_filename, "rb") as file:
                picture = discord.File(file)

                tarot_name = tarot_data[str(tarot_number)]["name"]
                upright_meaning = tarot_data[str(tarot_number)]["upright_position"]
                reverse_meaning = tarot_data[str(tarot_number)]["reverse_position"]
                roman_num = tarot_data[str(tarot_number)]["roman_num"]

                if is_reverse:
                    image = Image.open(file)
                    rotated_image = image.rotate(180)
                    rotated_image.save(image_filename)
                    rotated_picture = discord.File(image_filename)
                    await ctx.send(f"抽到的塔羅牌為 {roman_num}-{tarot_name}（逆位）\n逆位解釋: {reverse_meaning}", file=rotated_picture)
                    # 恢复图像到正位
                    image = rotated_image.rotate(180)
                    image.save(image_filename)
                else:
                    await ctx.send(f"抽到的塔羅牌為 {roman_num}-{tarot_name}（正位）\n正位解釋: {upright_meaning}", file=picture)
        except FileNotFoundError:
            await ctx.send(f"找不到編號為 {tarot_number} 的塔羅牌")

async def setup(bot):
    await bot.add_cog(Tarot(bot))
    print("Tarot.py is ready")
