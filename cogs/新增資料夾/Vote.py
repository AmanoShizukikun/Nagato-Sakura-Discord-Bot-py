import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from discord import SelectOption, SelectMenu, ButtonStyle

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voters = {}

    @commands.command(aliases=["votecreate","VOTECREATE","VoteC"])
    async def VoteCreate(self, ctx, question, *options):
        vote_data = {
            'question': question,
            'options': list(options),
            'votes': {option: 0 for option in options}
        }
        server_id = str(ctx.guild.id)
        server_folder = f'./server/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        vote_file = f'{server_folder}/Vote_{server_id}.json'
        with open(vote_file, 'w') as file:
            json.dump(vote_data, file, indent=4)
        await ctx.send("投票創建成功!")

    @commands.command(aliases=["vote","VOTE"])
    async def Vote(self, ctx, question, *options):
        server_id = str(ctx.guild.id)
        server_folder = f'./server/{server_id}'
        vote_file = f'{server_folder}/Vote_{server_id}.json'
        if not os.path.isfile(vote_file):
            await ctx.send("此問題的投票不存在。")
            return
        
        with open(vote_file, 'r') as file:
            vote_data = json.load(file)
        if question != vote_data['question']:
            await ctx.send("找不到符合的投票。")
            return
        
        voter_id = str(ctx.author.id)
        if voter_id in self.voters and self.voters[voter_id] == options:
            await ctx.send("你已經投過票了。")
            return
        
        if options[0] not in vote_data['options']:
            await ctx.send("投票選項不存在。")
            return
        
        vote_data['votes'][options[0]] += 1
        with open(vote_file, 'w') as file:
            json.dump(vote_data, file, indent=4)
        self.voters[voter_id] = True
        await ctx.send(f"你已成功為 '{options[0]}' 投票！")
        
    @commands.command(aliases=["voteresult","VOTERESULT","VoteR"])
    async def VoteResult(self, ctx, question):
        server_id = str(ctx.guild.id)
        server_folder = f'./server/{server_id}'
        vote_file = f'{server_folder}/Vote_{server_id}.json'
        
        if not os.path.isfile(vote_file):
            await ctx.send("此問題的投票不存在。")
            return
        
        with open(vote_file, 'r') as file:
            vote_data = json.load(file)

        if question != vote_data['question']:
            await ctx.send("找不到符合的投票。")
            return
        
        result_message = f"投票结果 for '{question}':\n"
        for option, count in vote_data['votes'].items():
            result_message += f"{option}: {count} 投票\n"
        await ctx.send(result_message)
        
    @VoteCreate.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("噫~糟糕！出現了一個錯誤：「格式輸入錯誤」請輸入正確的格式:!VoteCreate [問題] [選項1] [選項2] [選項N]")    
              
    @Vote.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("噫~糟糕！出現了一個錯誤：「格式輸入錯誤」請輸入正確的格式:!Vote [問題] [選項名稱]")             

    @VoteResult.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("噫~糟糕！出現了一個錯誤：「格式輸入錯誤」請輸入正確的格式:!VoteResult [問題]")
            
    @app_commands.command(name="votecreate", description="!VoteCreate [問題] [選項1] [選項2] [選項N] - 創建投票")  
    async def votecreate(self, interaction: discord.Interaction, question: str, options: str): 
        vote_data = {
            'question': question,
            'options': options.split(),
            'votes': {option: 0 for option in options.split()}
        }
        server_id = str(interaction.guild_id)
        server_folder = f'./server/{server_id}'
        os.makedirs(server_folder, exist_ok=True)
        vote_file = f'{server_folder}/Vote_{server_id}.json'
        with open(vote_file, 'w') as file:
            json.dump(vote_data, file, indent=4)
        await interaction.response.send_message(f"投票創建成功！\n 【問題】:{question} \n 【選項】{options.split()}")

    @app_commands.command(name="vote", description="!Vote [問題] [選項名稱] - 投票")
    async def vote(self, interaction: discord.Interaction, question: str, options: str):
        server_id = str(interaction.guild_id)
        server_folder = f'./server/{server_id}'
        vote_file = f'{server_folder}/Vote_{server_id}.json'
        if not os.path.isfile(vote_file):
            await interaction.response.send_message("此問題的投票不存在。")
            return

        with open(vote_file, 'r') as file:
            vote_data = json.load(file)
        if question != vote_data['question']:
            await interaction.response.send_message("找不到符合的投票。")
            return

        voter_id = str(interaction.user.id)
        if voter_id in self.voters and self.voters[voter_id] == options:
            await interaction.response.send_message("你已經投過票了。")
            return

        if options not in vote_data['options']:
            await interaction.response.send_message("投票選項不存在。")
            return

        vote_data['votes'][options] += 1
        with open(vote_file, 'w') as file:
            json.dump(vote_data, file, indent=4)
        self.voters[voter_id] = True
        await interaction.response.send_message(f"你已成功為 '{options}' 投票！")

    @app_commands.command(name="voteresult", description="!VoteResult [問題] - 查看投票結果")
    async def voteresult(self, interaction: discord.Interaction, question: str):
        server_id = str(interaction.guild_id)
        server_folder = f'./server/{server_id}'
        vote_file = f'{server_folder}/Vote_{server_id}.json'

        if not os.path.isfile(vote_file):
            await interaction.response.send_message("此問題的投票不存在。")
            return

        with open(vote_file, 'r') as file:
            vote_data = json.load(file)

        if question != vote_data['question']:
            await interaction.response.send_message("找不到符合的投票。")
            return

        result_message = f"投票结果 for '{question}':\n"
        for option, count in vote_data['votes'].items():
            result_message += f"{option}: {count} 投票\n"
        await interaction.response.send_message(result_message)               

async def setup(bot: commands.Bot):
    await bot.add_cog(Vote(bot))
    print("Vote.py is ready")