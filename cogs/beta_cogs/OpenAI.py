import discord
from discord.ext import commands
import openai
import os

openai.organization = "OpenAI 的 組織 ID"
openai.api_key = os.getenv("OpenAI 的 API 金鑰")

class OpenAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def OpenAI(self, ctx, *, content):
        try:
            # 將用戶輸入的內容傳遞給OpenAI的模型
            response = openai.Completion.create(
                engine="davinci",  # 選擇適合的引擎
                prompt=content,
                max_tokens=50  # 設定生成答案的最大長度
            )

            # 獲得AI的答覆
            ai_reply = response.choices[0].text

            # 將AI的答覆發送回Discord
            await ctx.send(f"AI回覆: {ai_reply}")
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")

async def setup(bot):
    await bot.add_cog(OpenAI(bot))
    print("OpenAI.py is ready")
