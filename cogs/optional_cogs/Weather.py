import discord
from discord import app_commands
from discord.ext import commands
import requests
import json

token = "CWA-93DC75ED-ACED-4F94-A28C-260480D30A6F" # 替換為您的API授權碼
locations = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
api_url = f"YOUR API"

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
                embed = discord.Embed(title="六都天氣預報", color=discord.Color.blue())
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
            
    @app_commands.command(name="weather", description="!Weather - 顯示六都的天氣預報")
    async def app_weather(self, interaction: discord.Interaction):
        try:
            req = requests.get(api_url)
            data = json.loads(req.text)
            if data["success"] == "true":
                reports = data["records"]["location"]
                embed = discord.Embed(title="六都天氣預報", color=discord.Color.blue())
        
                for report in reports:
                    location_name = report["locationName"]
                    if location_name in locations:
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
                            value = f":sunny: 天氣現象: {weather_description}\n:cloud_rain: 降雨機率: {rain_probability}\n:red_square: 最高溫: {max_temperature}\n:blue_square: 最低溫: {min_temperature}"
                            embed.add_field(name=location_name, value=value, inline=True)                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("無法獲取天氣預報。")
        except Exception as e:
            await interaction.response.send_message(f"發生錯誤：{e}")

    @app_commands.command(name="allweather", description="!AllWeather - 顯示所有縣市的天氣預報")
    async def app_allweather(self, interaction: discord.Interaction):
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
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("無法獲取天氣預報。")
        except Exception as e:
            await interaction.response.send_message(f"發生錯誤：{e}")
                
async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
    print("Weather.py is ready")