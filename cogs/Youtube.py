import discord
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
                        await self.send_single_song_embed(ctx, info, info['url'], info['channel'], info['title'], info['duration'], str(ctx.author))
    
                    if not ctx.voice_client.is_playing():
                        await self.play_next(ctx)
            except youtube_dl.DownloadError:
                await ctx.send("抱歉啊主人~長門櫻無法尋找或下載到該影片。請確認主人確認提供的網址是否有效。")
        else:
            await ctx.send("請主人先加入一個語音頻道再使用!Play來添加歌曲")
            
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
        embedMsg.set_thumbnail(url=video_info.get('thumbnail'))
        embedMsg.add_field(name="YouTube 頻道", value=channel_name, inline=False)
        embedMsg.add_field(name="YouTube 曲名", value=video_title, inline=False)
        embedMsg.add_field(name="曲目長度", value=video_length, inline=False)
        embedMsg.set_footer(text=f"添加者：{added_by}")
        await ctx.send(embed=embedMsg) 
            
    @commands.command(aliases=["JOIN","join"])
    async def Join(self, ctx):
        await self.join_voice_channel(ctx)

    @commands.command(aliases=["LEAVE","leave"])
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
            await ctx.send("目前沒有播放中的歌曲。")
    
async def setup(bot):
    await bot.add_cog(Youtube(bot))
    print("Youtube.py is ready")
