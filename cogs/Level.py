import discord
from discord import app_commands
from discord.ext import commands, tasks 
import json
import os
import math
import random
import asyncio

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.save())
        self.server_id = str(self.bot.guilds[0].id)
        self.server_folder = f'./server/{self.server_id}'
        os.makedirs(self.server_folder, exist_ok=True)
        self.Level_file = f'{self.server_folder}/Level_{self.server_id}.json'
        
        try:
            with open(self.Level_file, "r") as file:
                self.users = json.load(file)
        except FileNotFoundError:
            self.users = {}
      
    def Level_up(self, author_id):
        current_EXP = self.users[author_id]["EXP"]
        current_Level = self.users[author_id]["Lv"]
    
        if current_EXP >= math.ceil((50 * (current_Level **1.3))):
            self.users[author_id]["Lv"] +=1
            return True
        else:
            return False
    
    async def save(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            with open(self.Level_file, "w") as file:
                json.dump(self.users, file, indent=4)
            await asyncio.sleep(5)
  
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        author_id = str(message.author.id)
        if not author_id in self.users:
            self.users[author_id] = {}
            self.users[author_id]["Lv"] = 1
            self.users[author_id]["EXP"] = 0
        random_EXP = random.randint(5,10)
        self.users[author_id]["EXP"] += random_EXP
    
        if self.Level_up(author_id):
            Lv_up_embed = discord.Embed(title="恭喜主人等級上升啦~(≧▽≦)/ 好厲害呢！", color=discord.Color.green())
            Lv_up_embed.set_thumbnail(url=message.author.avatar.url)
            Lv_up_embed.add_field(name=f"恭喜!{message.author.name}提升等級至{self.users[author_id]['Lv']}等", value="")
            await message.channel.send(embed=Lv_up_embed)
    
    @commands.command(aliases=["LV","level"])
    async def Level(self,ctx,user: discord.User=None):
        if user is None:
            user = ctx.author
        elif user is not None:
            user = user
        roles = ', '.join([role.name for role in user.roles[1:]])  
        Lv_card = discord.Embed(title=f"{user.name}的個人資料卡",color=discord.Color.random()) 
        Lv_card.set_thumbnail(url=user.avatar.url)
        Lv_card.add_field(name=f"稱號: {roles}", value="", inline=False)
        Lv_card.add_field(name="角色等級: ", value=self.users[str(user.id)]['Lv'])
        Lv_card.add_field(name="角色經驗: ", value=self.users[str(user.id)]['EXP'])
        Lv_card.add_field(name="角色ID: ", value=f"{user.id}")
        Lv_card.add_field(name="加入伺服器日期", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
        await ctx.send(embed=Lv_card)
    
    @Level.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("噫~糟糕！出現了一個錯誤：「多於輸入」不開放查看別人的個人資料卡")      
            
    @app_commands.command(name="level", description="!Level [用戶] - 顯示[用戶]資料卡")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user
        roles = ', '.join([role.name for role in user.roles[1:]])  
        Lv_card = discord.Embed(title=f"{user.name}的個人資料卡", color=discord.Color.random()) 
        Lv_card.set_thumbnail(url=user.avatar.url)
        Lv_card.add_field(name=f"稱號: {roles}", value="", inline=False)
        Lv_card.add_field(name="角色等級: ", value=self.users[str(user.id)]['Lv'])
        Lv_card.add_field(name="角色經驗: ", value=self.users[str(user.id)]['EXP'])
        Lv_card.add_field(name="角色ID: ", value=f"{user.id}")
        Lv_card.add_field(name="加入伺服器日期", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
        await interaction.response.send_message(embed=Lv_card)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Level(bot))
    print("Level.py is ready")