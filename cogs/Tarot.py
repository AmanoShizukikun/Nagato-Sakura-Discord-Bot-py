import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import json
from PIL import Image
import tempfile

class Tarot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_tarot_info(self, ctx=None):
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
                tarot_info = tarot_data[str(tarot_number)]
                tarot_name = tarot_info["name"]
                upright_meaning = tarot_info["upright_position"]
                reverse_meaning = tarot_info["reverse_position"]
                roman_num = tarot_info["roman_num"]

                image = Image.open(file)
                if is_reverse:
                    image = image.rotate(180)
                    reverse_meaning, upright_meaning = upright_meaning, reverse_meaning

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                image.save(temp_file.name, "PNG")
                temp_file.close()

                return temp_file.name, f"{roman_num}-{tarot_name}", reverse_meaning if is_reverse else upright_meaning
        except FileNotFoundError:
            if ctx:
                await ctx.send(f"找不到編號為 {tarot_number} 的塔羅牌")
            else:
                print(f"找不到編號為 {tarot_number} 的塔羅牌")

    @commands.command(aliases=["tarot","TAROT"])
    async def Tarot(self, ctx):
        temp_file_path, name, meaning = await self.get_tarot_info(ctx)
        if temp_file_path:
            await ctx.send(f"抽到的塔羅牌為 {name}\n解釋: {meaning}", file=discord.File(temp_file_path))

    @app_commands.command(name="tarot", description="抽取塔羅牌")
    async def tarot(self, interaction: discord.Interaction):
        temp_file_path, name, meaning = await self.get_tarot_info()
        if temp_file_path:
            await interaction.response.send_message(f"抽到的塔羅牌為 {name}\n解釋: {meaning}", file=discord.File(temp_file_path))

async def setup(bot: commands.Bot):
    await bot.add_cog(Tarot(bot))
    print("Tarot.py is ready")
