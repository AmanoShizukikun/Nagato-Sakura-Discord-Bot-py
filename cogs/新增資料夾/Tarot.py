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

    async def get_tarot_info(self, ctx=None, interaction=None):
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

                tarot_info = tarot_data[str(tarot_number)]
                tarot_name = tarot_info["name"]
                upright_meaning = tarot_info["upright_position"]
                reverse_meaning = tarot_info["reverse_position"]
                roman_num = tarot_info["roman_num"]

                if is_reverse:
                    image = Image.open(file)
                    rotated_image = image.rotate(180)
                    rotated_image.save(image_filename)
                    rotated_picture = discord.File(image_filename)
                    if interaction:
                        await interaction.response.send_message(f"抽到的塔羅牌為 {roman_num}-{tarot_name}（逆位）\n逆位解釋: {reverse_meaning}", file=rotated_picture)
                    elif ctx:
                        await ctx.send(f"抽到的塔羅牌為 {roman_num}-{tarot_name}（逆位）\n逆位解釋: {reverse_meaning}", file=rotated_picture)
                    image = rotated_image.rotate(180)
                    image.save(image_filename)
                else:
                    if interaction:
                        await interaction.response.send_message(f"抽到的塔羅牌為 {roman_num}-{tarot_name}（正位）\n正位解釋: {upright_meaning}", file=picture)
                    elif ctx:
                        await ctx.send(f"抽到的塔羅牌為 {roman_num}-{tarot_name}（正位）\n正位解釋: {upright_meaning}", file=picture)
        except FileNotFoundError:
            if interaction:
                await interaction.response.send_message(f"找不到編號為 {tarot_number} 的塔羅牌")
            elif ctx:
                await ctx.send(f"找不到編號為 {tarot_number} 的塔羅牌")

    @commands.command(aliases=["tarot","TAROT"])
    async def Tarot(self, ctx):
        await self.get_tarot_info(ctx=ctx)

    @app_commands.command(name="tarot", description="!Tarot - 抽塔羅牌")
    async def tarot(self, interaction: discord.Interaction):
        await self.get_tarot_info(interaction=interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tarot(bot))
    print("Tarot.py is ready")