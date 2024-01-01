import discord
from discord.ext import commands
import socket

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["PING","ping"])
    async def Ping(self, ctx):
        bot_latency = round(self.bot.latency * 1000)
        await ctx.send(f"目前延遲為: {bot_latency} ms")     

    @commands.command()
    async def PingIP(self, ctx, hostname):
        try:
            ip_address = socket.gethostbyname(hostname)
            await ctx.send(f"網址 {hostname} 的 IP 地址為: {ip_address}")
        except socket.gaierror:
            await ctx.send("無法解析該網址或主機名稱")
            
async def setup(bot):
    await bot.add_cog(Ping(bot))
    print("Ping.py is ready")