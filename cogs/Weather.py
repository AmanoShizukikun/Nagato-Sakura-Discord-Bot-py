import discord
from discord.ext import commands
import requests
import json

token = "您的API授權碼" # 替換為您的API授權碼
locations = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
api_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWA-93DC75ED-ACED-4F94-A28C-260480D30A6F&format=JSON&locationName=&elementName=&sort=time"

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["weather","WEATHER","WX"])
    async def Weather(self, ctx, *location_name):
        try:
            req = requests.get(api_url)
            data = json.loads(req.text)
            if data["success"] == "true":
                reports = data["records"]["location"]
                embed = discord.Embed(title="天氣預報", color=discord.Color.blue())
                if not location_name:
                    reports = [location_data for location_data in reports if location_data["locationName"] in locations]
                else:
                    specific_location = " ".join(location_name)
                    reports = [location_data for location_data in reports if location_data["locationName"] == specific_location]
                for report in reports:
                    location_name = report["locationName"]
                    weather_element = report["weatherElement"]
                    weather_description = None
                    max_temperature = None
                    min_temperature = None
                    rain_probability = None
                    for element in weather_element:
                        if element["elementName"] == "Wx":
                            weather_description = element["time"][0]["parameter"]["parameterName"]
                        elif element["elementName"] == "MaxT":
                            max_temperature = element["time"][0]["parameter"]["parameterName"] + "°C"
                        elif element["elementName"] == "MinT":
                            min_temperature = element["time"][0]["parameter"]["parameterName"] + "°C"
                        elif element["elementName"] == "PoP":
                            rain_probability = element["time"][0]["parameter"]["parameterName"] + "%"
                    if weather_description is not None:
                        # 將兩個縣市並排顯示
                        value = f":sunny:天氣現象: {weather_description}\n:cloud_rain:降雨機率: {rain_probability}\n:red_square:最高溫: {max_temperature}\n:blue_square:最低溫: {min_temperature}"
                        embed.add_field(name=location_name, value=value, inline=True)                
                await ctx.send(embed=embed)
            else:
                await ctx.send("無法獲取天氣預報。")
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")
            
    @commands.command(aliases=["allweather","ALLWEATHER","AWX"])
    async def AllWeather(self, ctx):
        try:
            req = requests.get(api_url)
            data = json.loads(req.text)
            if data["success"] == "true":
                reports = data["records"]["location"]
                embed = discord.Embed(title="所有縣市天氣預報", color=discord.Color.blue())
                for report in reports:
                    location_name = report["locationName"]
                    weather_element = report["weatherElement"]
                    weather_description = None
                    max_temperature = None
                    min_temperature = None
                    rain_probability = None
                    for element in weather_element:
                        if element["elementName"] == "Wx":
                            weather_description = element["time"][0]["parameter"]["parameterName"]
                        elif element["elementName"] == "MaxT":
                            max_temperature = element["time"][0]["parameter"]["parameterName"] + "°C"
                        elif element["elementName"] == "MinT":
                            min_temperature = element["time"][0]["parameter"]["parameterName"] + "°C"
                        elif element["elementName"] == "PoP":
                            rain_probability = element["time"][0]["parameter"]["parameterName"] + "%"
                    if weather_description is not None:
                        value = f":sunny:天氣現象: {weather_description}\n:cloud_rain:降雨機率: {rain_probability}\n:red_square:最高溫: {max_temperature}\n:blue_square:最低溫: {min_temperature}"
                        embed.add_field(name=location_name, value=value, inline=True)                
                await ctx.send(embed=embed)
            else:
                await ctx.send("無法獲取天氣預報。")
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")   
            
    @Weather.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("噫~糟糕！出現了一個錯誤：「不存在的縣市」請輸入正確的縣市名稱")      
                
async def setup(bot):
    await bot.add_cog(Weather(bot))
    print("Weather.py is ready")