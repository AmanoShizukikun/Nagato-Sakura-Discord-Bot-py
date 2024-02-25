import discord
from discord.ext import commands
import random

class SnakeGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snake_head_emoji = '🐲'  
        self.snake_body_emoji = '🟩'  
        self.food_emoji = '🍎'
        self.directions = {'⬆️': (-1, 0), '⬇️': (1, 0), '⬅️': (0, -1), '➡️': (0, 1)}
        self.board_size = 4
        self.game_board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.snake_pos = [(0, 0)]
        self.food_pos = self.generate_food_position()
        self.game_over = False

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

async def setup(bot):
    await bot.add_cog(SnakeGame(bot))
    print("SnakeGame.py is ready")
