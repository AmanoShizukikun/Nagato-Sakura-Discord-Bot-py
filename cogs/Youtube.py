import discord
from discord import app_commands
from discord.ext import commands
import youtube_dl
import datetime
import time
import asyncio

FFMPEG_OPTS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice = None
        self.queue = []
        self.song_queue = {}
        self.now_playing = {}
        self.embed_color = 0xFF0000

    async def join_voice_channel(self, ctx_or_interaction):
        if isinstance(ctx_or_interaction, discord.Interaction):
            voice_channel = ctx_or_interaction.user.voice.channel
        else:
            voice_channel = ctx_or_interaction.author.voice.channel

        if voice_channel:
            self.voice = await voice_channel.connect()
            guild_id = ctx_or_interaction.guild.id if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.guild_id
            self.song_queue[guild_id] = []
            self.now_playing[guild_id] = None
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message("長門櫻已加入語音頻道")
            else:
                await ctx_or_interaction.send("長門櫻已加入語音頻道")
        else:
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message("請先加入一個語音頻道再使用!Join來邀請長門櫻喔~")
            else:
                await ctx_or_interaction.send("請主人先加入一個語音頻道再使用!Play來添加歌曲")

    async def leave_voice_channel(self, ctx_or_interaction):
        if self.voice and self.voice.is_connected():
            await self.voice.disconnect()
            guild_id = ctx_or_interaction.guild.id if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.guild_id
            self.song_queue.pop(guild_id, None)
            self.now_playing.pop(guild_id, None)
            self.queue.clear()
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send("長門櫻已離開語音頻道")
            else:
                await ctx_or_interaction.response.send_message("長門櫻已離開語音頻道")
        else:
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send("長門櫻未加入任何語音頻道")
            else:
                await ctx_or_interaction.response.send_message("長門櫻未加入任何語音頻道")
                
    async def play_join_voice_channel(self, ctx_or_interaction):
        if isinstance(ctx_or_interaction, discord.Interaction):
            voice_channel = ctx_or_interaction.user.voice.channel
        else:
            voice_channel = ctx_or_interaction.author.voice.channel

        if voice_channel:
            if not self.voice or not self.voice.is_connected():
                self.voice = await voice_channel.connect()
                guild_id = ctx_or_interaction.guild.id if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.guild_id
                self.song_queue[guild_id] = []
                self.now_playing[guild_id] = None
            else:
                self.voice.move_to(voice_channel)

    async def play_song(self, ctx_or_interaction, url):
        start_time = time.time()

        if not self.voice or not self.voice.is_connected():
            await self.play_join_voice_channel(ctx_or_interaction)

        if self.voice and self.voice.is_connected():
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': False,
                'quiet': True,
            }
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        for entry in info['entries']:
                            self.queue.append(entry)
                        end_time = time.time()
                        elapsed_time = round(end_time - start_time, 2)
                        if isinstance(ctx_or_interaction, discord.Interaction):
                            await ctx_or_interaction.response.send_message(f"長門櫻已添加 {len(info['entries'])} 首歌進佇列。（處理時間：{elapsed_time} 秒）")
                        else:
                            await ctx_or_interaction.send(f"長門櫻已添加 {len(info['entries'])} 首歌進佇列。（處理時間：{elapsed_time} 秒）")
                    else:
                        self.queue.append(info)
                        if isinstance(ctx_or_interaction, discord.Interaction):
                            await self.send_single_song_embed(ctx_or_interaction, info, info['url'], info['channel'], info['title'], info['duration'], str(ctx_or_interaction.user.display_name))
                        else:
                            await self.send_single_song_embed(ctx_or_interaction, info, info['url'], info['channel'], info['title'], info['duration'], str(ctx_or_interaction.author))

                    if not self.voice.is_playing():
                        await self.play_next(ctx_or_interaction)
            except youtube_dl.DownloadError:
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.response.send_message("抱歉啊主人~長門櫻無法尋找或下載到該影片。請確認主人確認提供的網址是否有效。")
                else:
                    await ctx_or_interaction.send("抱歉啊主人~長門櫻無法尋找或下載到該影片。請確認主人確認提供的網址是否有效。")
        else:
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message("請主人先加入一個語音頻道再使用!Play來添加歌曲")
            else:
                await ctx_or_interaction.send("請主人先加入一個語音頻道再使用!Play來添加歌曲")

    async def play_next(self, ctx_or_interaction, retry_count=3):
        if not self.voice or not self.voice.is_connected():
            return
        if self.voice.is_playing():
            while self.voice.is_playing():
                await asyncio.sleep(1)
        if self.queue:
            song_info = self.queue.pop(0)
            source = discord.FFmpegPCMAudio(song_info['url'], **FFMPEG_OPTS)
            self.voice.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx_or_interaction)))
            retries = 0
            while retries < retry_count:
                while self.voice.is_playing():
                    await asyncio.sleep(1)
                if self.voice.is_playing():
                    retries += 1
                else:
                    break
            if retries == retry_count:
                await ctx_or_interaction.send(f"抱歉啊主人，長門櫻嘗試播放音樂失敗，跳過 {song_info['title']}")
                await self.play_next(ctx_or_interaction)
        else:
            await ctx_or_interaction.send("主人的播放清單已播放完畢。長門櫻偷偷溜出了語音頻道。")
            await self.leave_voice_channel(ctx_or_interaction)

    async def send_single_song_embed(self, ctx_or_interaction, video_info, url, channel_name, video_title, video_length, added_by):
        video_length = str(datetime.timedelta(seconds=video_length))
        embedMsg = discord.Embed(
            title="正在播放",
            description=f"**[{video_title}]({url})**",
            color=self.embed_color
        )
        embedMsg.set_thumbnail(url=video_info.get('thumbnail'))
        embedMsg.add_field(name="YouTube 頻道", value=channel_name, inline=False)
        embedMsg.add_field(name="YouTube 曲名", value=video_title, inline=False)
        embedMsg.add_field(name="曲目長度", value=video_length, inline=False)
        embedMsg.set_footer(text=f"添加者：{added_by}")

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embedMsg)
        elif isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embedMsg)

    @commands.command(aliases=["JOIN", "join"])
    async def Join(self, ctx):
        await self.join_voice_channel(ctx)

    @commands.command(aliases=["LEAVE", "leave"])
    async def Leave(self, ctx):
        await self.leave_voice_channel(ctx)

    @commands.command(aliases=["PLAY", "play"])
    async def Play(self, ctx, *, url):
        await self.play_song(ctx, url)

    @commands.command(aliases=["LIST", "list"])
    async def List(self, ctx):
        if self.queue:
            embed = discord.Embed(title="主人目前的撥放清單~❤️", color=self.embed_color)
            number_of_songs = min(len(self.queue), 25)
            for index, info in enumerate(self.queue[:number_of_songs]):
                embed.add_field(name=f"{index + 1}. {info['title']}", value="", inline=False)
            if len(self.queue) > 25:
                embed.set_footer(text=f"長門櫻還有 {len(self.queue) - 25} 首歌曲未顯示")
            await ctx.send(embed=embed)
        else:
            await ctx.send("嗚嗚嗚~主人的撥放清單空空如也的呢!感緊添加幾首歌進去吧!")

    @commands.command(aliases=["SKIP", "skip"])
    async def Skip(self, ctx, amount: int = 1):
        if self.voice and self.voice.is_playing():
            amount = min(amount, len(self.queue))
            for _ in range(amount):
                self.voice.stop()
            await ctx.send(f"長門櫻已跳過 {amount} 首歌曲。")
        else:
            await ctx.send("很抱歉主人~目前沒有播放中的歌曲。")

    @app_commands.command(name="join", description="!Join - 長門櫻進入語音聊天室")
    async def join(self, interaction: discord.Interaction):
        await self.join_voice_channel(interaction)

    @app_commands.command(name="leave", description="!Leave - 長門櫻離開語音聊天室")
    async def leave(self, interaction: discord.Interaction):
        await self.leave_voice_channel(interaction)

    @app_commands.command(name="play", description="!Play [網址] - 長門櫻播放音樂(目前支援以下平台:Youtube)")
    async def play(self, interaction: discord.Interaction, url: str):
        await self.play_song(interaction, url)

    @app_commands.command(name="list", description="!List - 長門櫻顯示撥放清單")
    async def list(self, interaction: discord.Interaction):
        if self.queue:
            embed = discord.Embed(title="主人目前的撥放清單~❤️", color=self.embed_color)
            number_of_songs = min(len(self.queue), 25)
            for index, info in enumerate(self.queue[:number_of_songs]):
                embed.add_field(name=f"{index + 1}. {info['title']}", value="", inline=False)
            if len(self.queue) > 25:
                embed.set_footer(text=f"長門櫻還有 {len(self.queue) - 25} 首歌曲未顯示")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("嗚嗚嗚~主人的撥放清單空空如也的呢!感緊添加幾首歌進去吧!")

    @app_commands.command(name="skip", description="!Skip [數字] - 跳過 [數字] 首歌")
    async def skip(self, interaction: discord.Interaction, amount: int = 1):
        if self.voice and self.voice.is_playing():
            amount = min(amount, len(self.queue))
            for _ in range(amount):
                self.voice.stop()
            await interaction.response.send_message(f"長門櫻已跳過 {amount} 首歌曲。")
        else:
            await interaction.response.send_message("很抱歉主人~目前沒有播放中的歌曲。")

async def setup(bot: commands.Bot):
    await bot.add_cog(Youtube(bot))
    print("Youtube.py is ready")
