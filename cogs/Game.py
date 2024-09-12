import discord
from discord import app_commands
from discord.ext import commands
import random

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.secret_num = None
        self.guess = None
        self.guess_count = 0
        self.guess_limit = 3
        self.out_of_limit = False
        self.game_started = False
        
        self.snake_head_emoji = '🐲'  
        self.snake_body_emoji = '🟩'  
        self.food_emoji = '🍎'
        self.directions = {'⬆️': (-1, 0), '⬇️': (1, 0), '⬅️': (0, -1), '➡️': (0, 1)}
        self.board_size = 4
        self.game_board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.snake_pos = [(0, 0)]
        self.food_pos = self.generate_food_position()
        self.game_over = False

    @commands.command(aliases=["GGS","guessinggamestart","GUESSINGGAMESTART"])
    async def GuessingGameStart(self, ctx):
        if not self.game_started:
            self.secret_num = random.randint(0, 99)
            self.game_started = True
            await ctx.reply("主人~猜數字遊戲已經開始~❤ 請使用 `!Guess ` [數字] 來猜數字。")
        else:
            await ctx.reply("遊戲已經開始了，請繼續猜數字。")

    @commands.command(aliases=["GG","guess","GUESS"])
    async def Guess(self, ctx, number: int):
        if not self.game_started:
            await ctx.reply("主人~請先使用 `!GuessingGameStart` 命令來開始遊戲。")
            return

        self.guess_count += 1
        if self.guess_count <= self.guess_limit:
            self.guess = number
            if self.guess > self.secret_num:
                await ctx.reply("再小一點喔~❤")
            elif self.guess < self.secret_num:
                await ctx.reply("再大一點喔~❤")
        else:
            self.out_of_limit = True

        if self.out_of_limit or self.guess == self.secret_num:
            if self.out_of_limit:
                await ctx.reply(f"看來是你輸了主人！嘿嘿~正確答案是 {self.secret_num}~❤")
            else:
                await ctx.reply("恭喜主人你贏了~❤")
            self.reset_game()

    def reset_game(self):
        self.secret_num = None
        self.guess = None
        self.guess_count = 0
        self.out_of_limit = False
        self.game_started = False
        
    @Guess.error
    async def Guess_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("請輸入您想要猜的數字，正確的格式是：!Guess [數字] 喔~❤") 

    def generate_food_position(self):
        empty_cells = [(i, j) for i in range(self.board_size) for j in range(self.board_size) if (i, j) not in self.snake_pos]
        if not empty_cells:
            self.game_over = True
            return None
        return random.choice(empty_cells)

    async def draw_game_board(self, ctx):
        board_str = ''
        for i in range(self.board_size):
            for j in range(self.board_size):
                if (i, j) in self.snake_pos:
                    if (i, j) == self.snake_pos[-1]:  
                        board_str += self.snake_head_emoji
                    else:
                        board_str += self.snake_body_emoji
                elif (i, j) == self.food_pos:
                    board_str += self.food_emoji
                else:
                    board_str += '⬛'
            board_str += '\n'
    
        game_message = await ctx.send(board_str)

        for direction_emoji in self.directions.keys():
            await game_message.add_reaction(direction_emoji)

        return game_message

    def reset_game(self):
        self.snake_pos = [(0, 0)]
        self.food_pos = self.generate_food_position()
        self.game_over = False

    @commands.command(aliases=["snakegamereset", "SNAKEGAMERESET"])
    async def SnakeGameReset(self, ctx):
        self.reset_game()
        await ctx.send("遊戲已重置！")
        await self.draw_game_board(ctx)

    @commands.command(aliases=["SNAKEGAME","snakegame"])
    async def SnakeGame(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("請在伺服器內使用這個指令，而非私人頻道")
            return
    
        direction_message = await self.draw_game_board(ctx)  

        while not self.game_over:
            for direction_emoji in self.directions.keys():  
                await direction_message.add_reaction(direction_emoji)  

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) in self.directions.keys() and reaction.message.id == direction_message.id

            reaction, user = await self.bot.wait_for('reaction_add', check=check)
            await direction_message.clear_reactions()

            next_row, next_col = self.snake_pos[-1][0] + self.directions[str(reaction.emoji)][0], \
                                 self.snake_pos[-1][1] + self.directions[str(reaction.emoji)][1]

            if next_row < 0 or next_row >= self.board_size or next_col < 0 or next_col >= self.board_size \
                    or (next_row, next_col) in self.snake_pos:
                await ctx.send("遊戲結束！")
                self.game_over = True
                break

            if (next_row, next_col) == self.food_pos:
                self.snake_pos.append((next_row, next_col))
                self.food_pos = self.generate_food_position()
                if self.game_over:
                    await ctx.send("恭喜主人贏了遊戲！")
            else:
                self.snake_pos.pop(0)
                self.snake_pos.append((next_row, next_col))

            direction_message = await self.draw_game_board(ctx)
            
    @app_commands.command(name="guessinggamestart", description="!GuessingGameStart - 開啟猜數字遊戲")
    async def guessinggamestart(self, interaction: discord.Interaction):
        if not self.game_started:
            self.secret_num = random.randint(0, 99)
            self.game_started = True
            await interaction.response.send_message("主人~猜數字遊戲已經開始~❤ 請使用 `!Guess ` [數字] 來猜數字。")
        else:
            await interaction.response.send_message("遊戲已經開始了，請繼續猜數字。")
            
    @app_commands.command(name="guess", description="!Guess [數字] - 猜數字")
    async def guess(self, interaction: discord.Interaction, number: int):
        if not self.game_started:
            await interaction.response.send_message("主人~請先使用 `!GuessingGameStart` 命令來開始遊戲。")
            return

        self.guess_count += 1
        if self.guess_count <= self.guess_limit:
            self.guess = number
            if self.guess > self.secret_num:
                await interaction.response.send_message("再小一點喔~❤")
            elif self.guess < self.secret_num:
                await interaction.response.send_message("再大一點喔~❤")
        else:
            self.out_of_limit = True

        if self.out_of_limit or self.guess == self.secret_num:
            if self.out_of_limit:
                await interaction.response.send_message(f"看來是你輸了主人！嘿嘿~正確答案是 {self.secret_num}~❤")
            else:
                await interaction.response.send_message("恭喜主人你贏了~❤")
            self.reset_game()
            
async def setup(bot: commands.Bot):
    await bot.add_cog(Game(bot))
    print("Game.py is ready")