import discord
from discord.ext import commands
import random
import os
import datetime

class FestivalEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["festivalevent","FESTIVALEVENT"])
    async def FestivalEvent(self, ctx):
        current_date = datetime.datetime.now().date()

        festivals = {
            "NewYear": (datetime.date(current_date.year, 12, 31), datetime.date(current_date.year + 1, 2)),
            "AdultDay": (datetime.date(current_date.year, 1, 8), datetime.date(current_date.year, 1, 10)),
            "Valentine": (datetime.date(current_date.year, 2, 13), datetime.date(current_date.year, 2, 15)),
            "OceanDay": (datetime.date(current_date.year, 7, 14), datetime.date(current_date.year, 7, 18)),
            "MountainDay": (datetime.date(current_date.year, 8, 10), datetime.date(current_date.year, 8, 13)),
            "ObonFestival": (datetime.date(current_date.year, 8, 14), datetime.date(current_date.year, 8, 17)),
            "SportsDay": (datetime.date(current_date.year, 10, 8), datetime.date(current_date.year, 10, 9)),
            "Halloween": (datetime.date(current_date.year, 10, 30), datetime.date(current_date.year, 11, 2)),
            "Christmas": (datetime.date(current_date.year, 12, 23), datetime.date(current_date.year, 12, 26))
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
                    with open(image_path, 'rb') as f:
                        picture = discord.File(f)
                    await ctx.send(file=picture)
                else:
                    await ctx.send(f"抱歉啊~主人!長門櫻找不到{current_festival}時的照片。")
            else:
                await ctx.send(f"抱歉啊~主人!長門櫻找不到{current_festival}相關的資料夾。")
        else:
            await ctx.send("主人~長門櫻今天沒有任何活動。")

async def setup(bot):
    await bot.add_cog(FestivalEvent(bot))
    print("FestivalEvent.py is ready")
