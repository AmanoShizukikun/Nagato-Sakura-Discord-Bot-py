import discord
from discord.ext import commands
import youtube_dl
import datetime
import time
import asyncio
import requests

FFMPEG_OPTS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice = None
        self.queue = []
        self.song_queue = {}
        self.now_playing = {}
        self.embed_color = 0xFF0000

    async def join_voice_channel(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            self.voice = await ctx.author.voice.channel.connect()
            self.song_queue[ctx.guild.id] = []
            self.now_playing[ctx.guild.id] = None
        else:
            await ctx.send("請先加入一個語音頻道")

    async def leave_voice_channel(self, ctx):
        if self.voice and self.voice.is_connected():
            await self.voice.disconnect()
            guild_id = ctx.guild.id
            self.song_queue.pop(guild_id, None)
            self.now_playing.pop(guild_id, None)
            self.queue.clear()
        else:
            await ctx.send("長門櫻未加入任何語音頻道")

    async def play_song(self, ctx, url):
        start_time = time.time()

        if not self.voice or not self.voice.is_connected():
            await self.join_voice_channel(ctx)

        if self.voice and self.voice.is_connected():
            if "youtube.com" in url or "youtu.be" in url:
                await self.play_youtube_song(ctx, url, start_time)
            elif "streetvoice.com" in url:
                await self.play_streetvoice_song(ctx, url, start_time)
            else:
                await ctx.send("抱歉，目前只支援 YouTube 和 StreetVoice 這兩個平台。")

    async def play_youtube_song(self, ctx, url, start_time):
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
                    await ctx.send(f"長門櫻已添加 {len(info['entries'])} 首歌進佇列。（處理時間：{elapsed_time} 秒）")
                else:
                    self.queue.append(info)
                    await self.send_single_song_embed(ctx, info, info['url'], info['channel'], info['title'],
                                                      info['duration'], str(ctx.author))

                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)
        except youtube_dl.DownloadError:
            await ctx.send("抱歉啊主人~長門櫻無法尋找或下載到該影片。請確認主人確認提供的網址是否有效.")

    async def play_streetvoice_song(self, ctx, url, start_time):
        song_info = self.find(url)
        if song_info:
            u_song = song_info[1], song_info[0]
            u_song += (ctx.author.id,)
            if ctx.guild.id not in self.song_queue:
                self.song_queue[ctx.guild.id] = [u_song]
            else:
                self.song_queue[ctx.guild.id].append(u_song)
            await ctx.send("已添加進佇列")
            if not ctx.voice_client.is_playing():
                await self.check_queue_and_play_next_if_have_next(ctx)
        else:
            await ctx.send("無法獲取 StreetVoice 歌曲信息或該歌曲無法播放。")

    async def play_next(self, ctx, retry_count=3):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return
        if ctx.voice_client and ctx.voice_client.is_playing():
            while ctx.voice_client.is_playing():
                await asyncio.sleep(1)
        if self.queue and ctx.voice_client:
            song_info = self.queue.pop(0)
            source = discord.FFmpegPCMAudio(song_info['url'], **FFMPEG_OPTS)
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            retries = 0
            while retries < retry_count:
                while ctx.voice_client.is_playing():
                    await asyncio.sleep(1)
                if ctx.voice_client.is_playing():
                    retries += 1
                else:
                    break
            if retries == retry_count:
                await ctx.send(f"播放失敗，跳過 {song_info['title']}")
                await self.play_next(ctx)
        else:
            await ctx.send("播放清單為空。長門櫻將離開語音頻道。")
            await self.leave_voice_channel(ctx)

    async def send_single_song_embed(self, ctx, video_info, url, channel_name, video_title, video_length, added_by):
        video_length = str(datetime.timedelta(seconds=video_length))
        embedMsg = discord.Embed(
            title="正在播放",
            description=f"**[{video_title}]({url})**",
            color=self.embed_color
        )
        if 'thumbnail' in video_info:
            embedMsg.set_thumbnail(url=video_info.get('thumbnail'))
        embedMsg.add_field(name="音樂來自", value=channel_name, inline=False)
        embedMsg.add_field(name="音樂名稱", value=video_title, inline=False)
        embedMsg.add_field(name="音樂長度", value=video_length, inline=False)
        embedMsg.set_footer(text=f"添加者：{added_by}")
        await ctx.send(embed=embedMsg)

    async def check_queue_and_play_next_if_have_next(self, ctx: commands.Context):
        voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)

        if ctx.guild.id in self.song_queue and self.song_queue[ctx.guild.id]:
            if voice and self.now_playing.get(ctx.guild.id) != self.song_queue[ctx.guild.id][0]:
                u_song = self.song_queue[ctx.guild.id].pop(0)
                self.now_playing[ctx.guild.id] = u_song
                try:
                    voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS),
                            after=lambda e: self.bot.loop.create_task(self.check_queue_and_play_next_if_have_next(ctx)))
                    await self.send_single_song_embed(ctx, {}, u_song[1], "StreetVoice", u_song[1], 0, ctx.author.id)
                except Exception as e:
                    await ctx.send(f"播放失敗: {e}")
                    self.now_playing[ctx.guild.id] = None
                    await self.check_queue_and_play_next_if_have_next(ctx)
            else:
                await self.check_queue_and_play_next_if_have_next(ctx)
        elif voice and voice.is_connected():
            await ctx.send("已離開語音頻道.")
            
    def find(self, url: str):
        if url.startswith(("https://streetvoice.com/", "http://streetvoice.com/")):
            s = url.split("/")
            s = list(filter(None, s))
            if s[-1].isnumeric and s[-2] == "songs":
                return self.streetvoice(s[-1]), self.streetvoice_title(s[-1]), url

        return None

    def streetvoice(self, id: str):
        try:
            r = requests.post(f"https://streetvoice.com/api/v4/song/{id}/hls/file/", data={})
            r.raise_for_status()
            return r.json()['file']
        except requests.exceptions.RequestException as e:
            print(f"StreetVoice請求錯誤: {e}")
            return None

    def streetvoice_title(self, id: str):
        try:
            r = requests.get(f"https://streetvoice.com/api/v4/song/{id}")
            r.raise_for_status()
            return r.json()['name']
        except requests.exceptions.RequestException as e:
            print(f"StreetVoice請求錯誤: {e}")
            return None

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
            embed = discord.Embed(title="目前的撥放清單", color=self.embed_color)
            number_of_songs = min(len(self.queue), 25)
            for index, info in enumerate(self.queue[:number_of_songs]):
                embed.add_field(name=f"{index + 1}. {info['title']}", value="", inline=False)
            if len(self.queue) > 25:
                embed.set_footer(text=f"還有 {len(self.queue) - 25} 首歌曲未顯示")
            await ctx.send(embed=embed)
        else:
            await ctx.send("撥放清單為空")

    @commands.command(aliases=["SKIP", "skip"])
    async def Skip(self, ctx, amount: int = 1):
        if self.voice and self.voice.is_playing():
            amount = min(amount, len(self.queue))
            for _ in range(amount):
                self.voice.stop()
            await ctx.send(f"已跳過 {amount} 首歌曲。")
        else:
            await ctx.send("目前沒有播放中的歌曲.")

async def setup(bot):
    await bot.add_cog(MusicPlayer(bot))
    print("MusicPlayer.py is ready")
