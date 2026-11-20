import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import datetime

class FestivalEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_festival_image(self, ctx, interaction, image_path):
        with open(image_path, 'rb') as f:
            picture = discord.File(f)
            if ctx:
                await ctx.send(file=picture)
            elif interaction:
                await interaction.response.send_message(file=picture)

    async def check_and_send_festival_image(self, ctx, interaction):
        current_date = datetime.datetime.now().date()

        festivals = {
            "NewYear": (datetime.date(current_date.year, 1, 1), datetime.date(current_date.year, 1, 1)),
            "AdultDay": (datetime.date(current_date.year, 1, 9), datetime.date(current_date.year, 1, 9)),
            "Valentine": (datetime.date(current_date.year, 2, 14), datetime.date(current_date.year, 2, 14)),
            "CatDay": (datetime.date(current_date.year, 2, 22), datetime.date(current_date.year, 2, 22)),
            "GirlsDay": (datetime.date(current_date.year, 3, 3), datetime.date(current_date.year, 3, 3)),
            "Easter": (datetime.date(current_date.year, 3, 24), datetime.date(current_date.year, 3, 24)),
            "AprilFools": (datetime.date(current_date.year, 4, 1), datetime.date(current_date.year, 4, 1)),
            "ChildrensDayJP": (datetime.date(current_date.year, 5, 5), datetime.date(current_date.year, 5, 5)),
            "DragonBoatFestival": (datetime.date(current_date.year, 5, 19), datetime.date(current_date.year, 5, 19)),
            "Tanabata": (datetime.date(current_date.year, 7, 7), datetime.date(current_date.year, 7, 7)),
            "OceanDay": (datetime.date(current_date.year, 7, 17), datetime.date(current_date.year, 7, 17)),
            "MeowDay": (datetime.date(current_date.year, 8, 1), datetime.date(current_date.year, 8, 1)),
            "UnderwearDay": (datetime.date(current_date.year, 8, 2), datetime.date(current_date.year, 8, 2)),
            "MountainDay": (datetime.date(current_date.year, 8, 11), datetime.date(current_date.year, 8, 11)),
            "ObonFestival": (datetime.date(current_date.year, 8, 13), datetime.date(current_date.year, 8, 16)),
            "PlayboyBunnyDay": (datetime.date(current_date.year, 8, 21), datetime.date(current_date.year, 8, 23)),
            "SistersDay": (datetime.date(current_date.year, 12, 6), datetime.date(current_date.year, 12, 6)),
            "WinterSolstice": (datetime.date(current_date.year, 12, 22), datetime.date(current_date.year, 12, 22)),
            "Christmas": (datetime.date(current_date.year, 12, 24), datetime.date(current_date.year, 12, 25)),
            "DaughtersDay": (datetime.date(current_date.year, 3, 3), datetime.date(current_date.year, 3, 3)),
            "SportsDay": (datetime.date(current_date.year, 10, 9), datetime.date(current_date.year, 10, 9)),
            "MothersDay": (datetime.date(current_date.year, 9, 6), datetime.date(current_date.year, 9, 6)),
            "MoonFestival": (datetime.date(current_date.year, 5, 19), datetime.date(current_date.year, 5, 19)),
            "LolitaDay": (datetime.date(current_date.year, 10, 11), datetime.date(current_date.year, 10, 11)),
            "Halloween": (datetime.date(current_date.year, 10, 31), datetime.date(current_date.year, 11, 1)),
            "CultureDay": (datetime.date(current_date.year, 11, 3), datetime.date(current_date.year, 11, 3)),
            "VeteransDay": (datetime.date(current_date.year, 11, 11), datetime.date(current_date.year, 11, 11)),
            "Thanksgiving": (datetime.date(current_date.year, 11, 26), datetime.date(current_date.year, 11, 26)),
            "AbsoluteTerritoryDay": (datetime.date(current_date.year, 11, 28), datetime.date(current_date.year, 11, 28)),
            "DoubleNinthFestival": (datetime.date(current_date.year, 9, 9), datetime.date(current_date.year, 9, 9)),
            "TeachersDay": (datetime.date(current_date.year, 9, 28), datetime.date(current_date.year, 9, 28))
        }

        current_festival = None
        for festival, (start_date, end_date) in festivals.items():
            if start_date <= current_date <= end_date:
                current_festival = festival
                break

        if current_festival:
            festival_folder = os.path.abspath(f'./data/FestivalEvent/{current_festival}/')
            if os.path.exists(festival_folder):
                festival_images = [f for f in os.listdir(festival_folder) if f.endswith('.jpg') or f.endswith('.png')]
                if festival_images:
                    image_name = random.choice(festival_images)
                    image_path = os.path.join(festival_folder, image_name)
                    await self.send_festival_image(ctx, interaction, image_path)
                else:
                    message = f"抱歉啊~主人!長門櫻找不到{current_festival}時的照片。"
                    if ctx:
                        await ctx.send(message)
                    elif interaction:
                        await interaction.response.send_message(message)
            else:
                message = f"抱歉啊~主人!長門櫻找不到{current_festival}相關的資料夾。"
                if ctx:
                    await ctx.send(message)
                elif interaction:
                    await interaction.response.send_message(message)
        else:
            message = "主人~長門櫻今天沒有任何活動。"
            if ctx:
                await ctx.send(message)
            elif interaction:
                await interaction.response.send_message(message)
            
    @commands.command(aliases=["festivalevent","FESTIVALEVENT"])
    async def FestivalEvent(self, ctx):
        await self.check_and_send_festival_image(ctx, None)

    @app_commands.command(name="festivalevent", description="!FestivalEvent - 當特殊的日子來臨之時會有彩蛋")
    async def festivalevent(self, interaction: discord.Interaction):
        await self.check_and_send_festival_image(None, interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(FestivalEvent(bot))
    print("FestivalEvent.py is ready")
