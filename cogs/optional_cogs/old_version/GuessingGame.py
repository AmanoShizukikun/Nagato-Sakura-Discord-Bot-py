import discord
from discord.ext import commands
import random

class GuessingGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.secret_num = None
        self.guess = None
        self.guess_count = 0
        self.guess_limit = 3
        self.out_of_limit = False
        self.game_started = False

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

async def setup(bot):
    await bot.add_cog(GuessingGame(bot))
    print("GuessingGame.py is ready")