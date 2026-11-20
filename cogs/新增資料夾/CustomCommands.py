import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import json
import os

class CustomCommands(commands.Cog):
    def __init__(self, bot, guild_id: Optional[int] = None):
        self.bot = bot
        
    @commands.command(aliases=["add","ADD"])
    async def Add(self, ctx, command_name: str, *, command_content: str):
        server_id = str(ctx.guild.id)
        subfolder = "server"
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")
        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
        except FileNotFoundError:
            custom_commands = {}
        custom_commands[command_name] = command_content
        with open(file_name, "w") as file:
            json.dump(custom_commands, file, indent=4)
        await ctx.send(f"已經成功新增了自訂指令：!{command_name} 了喔~（^^） 有其他需要我幫忙的嗎？❤")
    
    @commands.command(aliases=["edit","EDIT"])
    async def Edit(self, ctx, command_name: str, *, new_command_content: str):
        server_id = str(ctx.guild.id)
        subfolder = "server"
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")

        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
        except FileNotFoundError:
            await ctx.send("這個伺服器還沒有自訂指令，無法編輯喔~ >.<")
            return
        if command_name in custom_commands:
            custom_commands[command_name] = new_command_content
            with open(file_name, "w") as file:
                json.dump(custom_commands, file, indent=4)
            await ctx.send(f"已經成功更新了自訂指令 !{command_name} 的內容更新為 {new_command_content} 了喔~（^^）❤。")
        else:
            await ctx.send(f"嗚嗚~找不到指令了喔 >.<：!{command_name}")
            
    @commands.command(aliases=["remove","REMOVE"])
    async def Remove(self, ctx, command_name: str):
        server_id = str(ctx.guild.id)
        subfolder = "server"
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")

        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
        except FileNotFoundError:
            await ctx.send("這個伺服器還沒有自訂指令，無法刪除喔~ >.<")
            return
        if command_name in custom_commands:
            del custom_commands[command_name]
            with open(file_name, "w") as file:
                json.dump(custom_commands, file, indent=4)
            await ctx.send(f"已經成功刪除了自訂指令 !{command_name} 了喔~（^^）❤")
        else:
            await ctx.send(f"嗚嗚~找不到指令了喔 >.<：!{command_name}")  
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and message.content.startswith("!") and message.guild:
            command_name = message.content[1:]
            server_id = str(message.guild.id)
            subfolder = "server"
            server_folder = f'./{subfolder}/{server_id}'
            os.makedirs(server_folder, exist_ok=True)
            file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")
            try:
                with open(file_name, "r") as file:
                    custom_commands = json.load(file)
                if command_name in custom_commands:
                    command_content = custom_commands[command_name]
                    await message.channel.send(command_content)
            except FileNotFoundError:
                pass
            
    @commands.command()
    async def get_custom_command(self, ctx, command_name: str):
        server_id = str(ctx.guild.id)
        subfolder = "server" 
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json") 
        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
            if command_name in custom_commands:
                command_content = custom_commands[command_name]
                await ctx.reply(command_content)
            else:
                await ctx.reply(f"嗚嗚~找不到指令了喔 >.<：!{command_name}")
        except FileNotFoundError:
            await ctx.reply("這個伺服器目前還沒有自訂指令呢~ >.< 有其他我可以為您做的嗎？（^^） ❤")
            
    @Add.error
    async def Add_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("主人~請輸入您想要添加的指令，正確的格式應該是：!Add [指令名稱] [指令內容] 才對喔~❤") 
      
    @Edit.error
    async def Edit_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("主人~如果您想要編輯就的指令，正確的格式應該是：!Edit [指令名稱] [指令內容] 才對喔~❤") 
      
    @Remove.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("嗚嗚~主人~你想刪除指令嗎，正確的格式應該是：!Remove [指令名稱] 才對喔~❤") 
            
    @app_commands.command(name="add", description="!Add [指令名稱] [指令內容] - 新增自訂指令")
    async def add(self, interaction, command_name: str, *, command_content: str):
        server_id = str(interaction.guild.id)
        subfolder = "server" 
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")
        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
        except FileNotFoundError:
            custom_commands = {}
        custom_commands[command_name] = command_content
        with open(file_name, "w") as file:
            json.dump(custom_commands, file, indent=4)
        await interaction.response.send_message(f"已經成功新增了自訂指令：!{command_name} 了喔~（^^） 有其他需要我幫忙的嗎？❤")
        
    @app_commands.command(name="edit", description="!Edit [指令名稱] [新的指令內容] - 編輯自訂指令")
    async def edit(self, interaction, command_name: str, *, new_command_content: str):
        server_id = str(interaction.guild.id)
        subfolder = "server"
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")

        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
        except FileNotFoundError:
            await interaction.response.send_message("這個伺服器還沒有自訂指令，無法編輯喔~ >.<")
            return
        if command_name in custom_commands:
            custom_commands[command_name] = new_command_content
            with open(file_name, "w") as file:
                json.dump(custom_commands, file, indent=4)
            await interaction.response.send_message(f"已經成功更新了自訂指令 !{command_name} 的內容更新為 {new_command_content} 了喔~（^^）❤。")
        else:
            await interaction.response.send_message(f"嗚嗚~找不到指令了喔 >.<：!{command_name}")
            
    @app_commands.command(name="remove", description="!Remove [指令名稱] - 刪除自訂指令")
    async def remove(self, interaction, command_name: str):
        server_id = str(interaction.guild.id)
        subfolder = "server"
        server_folder = f'./{subfolder}/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        file_name = os.path.join(server_folder, f"CustomCommands_{server_id}.json")

        try:
            with open(file_name, "r") as file:
                custom_commands = json.load(file)
        except FileNotFoundError:
            await interaction.response.send_message("這個伺服器還沒有自訂指令，無法刪除喔~ >.<")
            return
        if command_name in custom_commands:
            del custom_commands[command_name]
            with open(file_name, "w") as file:
                json.dump(custom_commands, file, indent=4)
            await interaction.response.send_message(f"已經成功刪除了自訂指令 !{command_name} 了喔~（^^）❤")
        else:
            await interaction.response.send_message(f"嗚嗚~找不到指令了喔 >.<：!{command_name}")

async def setup(bot: commands.Bot):
    await bot.add_cog(CustomCommands(bot))
    print("CustomCommands.py is ready")
    