import discord
from discord import app_commands
from discord.ext import commands
import socket

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["PING","ping"])
    async def Ping(self, ctx):
        bot_latency = round(self.bot.latency * 1000)
        await ctx.send(f"目前延遲為: {bot_latency} ms")     

    @commands.command(aliases=["PINGIP","pingip"])
    async def PingIP(self, ctx, hostname):
        try:
            ip_address = socket.gethostbyname(hostname)
            await ctx.send(f"網址 {hostname} 的 IP 地址為: {ip_address}")
        except socket.gaierror:
            await ctx.send("無法解析該網址或主機名稱")
            
    @app_commands.command(name="ping", description="!Ping - 長門櫻在Discord WebSocket協議的延遲")
    async def ping(self, interaction: discord.Interaction):
        bot_latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"目前延遲為: {bot_latency} ms")
        
    @app_commands.command(name="pingip", description="!PingIP [網址] - 查詢網站 IP")
    async def pingip(self, interaction: discord.Interaction, hostname: str):
        try:
            ip_address = socket.gethostbyname(hostname)
            await interaction.response.send_message(f"網址 {hostname} 的 IP 地址為: {ip_address}")
        except socket.gaierror:
            await interaction.response.send_message("無法解析該網址或主機名稱")
            
async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
    print("Ping.py is ready")