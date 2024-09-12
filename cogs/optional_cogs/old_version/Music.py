import discord
from discord.ext import commands
import requests
import youtube_dl
from youtube_dl import YoutubeDL
import asyncio

embed_color = 0xFF0000
song_queue = {}
now_playing = {}
skip_vote = {}

FFMPEG_OPTS = {
    'options': '-vn',  
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_check(self, ctx):
        if ctx.guild:
            if ctx.command.name in ["play", "join", "leave", "list"]:
                return commands.cooldown(1, 2, commands.BucketType.guild)
        return True
        
    async def check_queue_and_play_next_if_have_next(self, ctx: commands.Context):
        if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
            voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            if now_playing.get(ctx.guild.id) != song_queue[ctx.guild.id][0]:
                u_song = song_queue[ctx.guild.id].pop(0)
                now_playing[ctx.guild.id] = u_song
                skip_vote[ctx.guild.id] = []
                try:
                    voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS),
                               after=lambda e: self.bot.loop.create_task(self.check_queue_and_play_next_if_have_next(ctx)))
                    embedMsg = discord.Embed(title="現正播放",
                                             description=f"**[{u_song[1]}]({u_song[2]})**",
                                             color=embed_color)
                    await ctx.send(embed=embedMsg)
                except Exception as e:
                    print(f"播放歌曲時出錯: {e}")
                    await ctx.send("播放歌曲時出錯。")
        
    async def send_message_with_retry(self, ctx, message_content):
        retry_count = 0
        while retry_count < 3:
            try:
                await ctx.send(message_content)
                break  # 如果成功，退出循環
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after
                    print(f"速率限制。{retry_after} 秒後重試。")
                    await asyncio.sleep(retry_after)
                    retry_count += 1
                else:
                    print(f"無法發送消息：{e}")
                    break
        
    @commands.command(aliases=["JOIN","join"])
    async def Join(self, ctx):
        if ctx.author.voice:
            vc = ctx.author.voice.channel
            if ctx.voice_client is None:
                await vc.connect()
            else:
                await vc.move()
        else:
            embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)

    @commands.command(aliases=["LEAVE","leave"])
    async def Leave(self, ctx):
        if ctx.author.voice and ctx.voice_client.channel:
            if ctx.author.voice.channel.id == ctx.voice_client.channel.id:
                voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
                voice.stop()
                now_playing[ctx.guild.id] = None
                song_queue[ctx.guild.id] = []
                skip_vote[ctx.guild.id] = []
                await ctx.voice_client.disconnect()
            else:
                embedMsg = discord.Embed(description="你必須在該語音頻道內才能使用此指令", color=embed_color)
                await ctx.reply(embed=embedMsg)
        else:
            embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)         
    
    @commands.command(aliases=["PLAY", "play"])
    async def Play(self, ctx, url: str):
        result = self.find(url)
        if not ctx.voice_client or not ctx.voice_client.is_connected():
        # 如果沒有連接到語音頻道，則進行連接
            if ctx.author.voice:
                vc = ctx.author.voice.channel
                await vc.connect()
            else:
                embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
                await ctx.reply(embed=embedMsg)
                return
    
    # 確認是否在正確的語音頻道
        if ctx.voice_client.channel != ctx.author.voice.channel:
            embedMsg = discord.Embed(description="你必須在相同的語音頻道才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)
            return
        if not ctx.voice_client:  # 機器人沒在語音頻道內
            vc = ctx.author.voice.channel
            await vc.connect()
        if not ctx.voice_client.is_playing():
            await self.check_queue_and_play_next_if_have_next(ctx)
        voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)

    # 如果是YouTube播放清單
        if "list" in url:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'extract_flat': True,
                'force_generic_extractor': True,
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                if 'entries' in info_dict:
                    for entry in info_dict['entries']:
                        song_url = entry['url']
                        u_song = self.find(song_url)
                        if u_song is not None and u_song != 0 and u_song[0]:
                            u_song += (ctx.author.id,)
                            if ctx.guild.id not in song_queue:
                                song_queue[ctx.guild.id] = [u_song]
                            else:
                                song_queue[ctx.guild.id].append(u_song)
                    await ctx.send(f"已添加 {len(info_dict['entries'])} 首歌進佇列.")
                    if not ctx.voice_client.is_playing():
                        self.check_queue_and_play_next_if_have_next(ctx)              
                else:
                    song_url = info_dict['formats'][0]['url']
                    u_song = self.find(song_url)
                    if u_song is not None and u_song != 0 and u_song[0]:
                        u_song += (ctx.author.id,)
                        if ctx.guild.id not in song_queue:
                            song_queue[ctx.guild.id] = [u_song]
                        else:
                            song_queue[ctx.guild.id].append(u_song)
                        await ctx.send("已添加進佇列")
                        if not ctx.voice_client.is_playing():
                            self.check_queue_and_play_next_if_have_next(ctx)
                    else:
                        embedMsg = discord.Embed(description="無法獲取播放清單的信息", color=embed_color)
                        await ctx.send(embed=embedMsg)

        else:
            u_song = self.find(url)
            if u_song is not None and u_song != 0 and u_song[0]:
                if ctx.guild.id not in song_queue or not song_queue[ctx.guild.id]:
                    now_playing[ctx.guild.id] = u_song
                    voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS),
                            after=lambda e: self.check_queue_and_play_next_if_have_next(ctx))
                    skip_vote[ctx.guild.id] = []
                    video_info = self.get_youtube_video_info(url)
                    if video_info:
                        channel_name = video_info.get('channel_name')
                    video_title = video_info.get('video_title')
                    video_length = video_info.get('video_length')
                    added_by = ctx.author.name
                    embedMsg = discord.Embed(title="正在播放",
                                            description=f"**[{u_song[1]}]({url})**",
                                            color=embed_color)
                    embedMsg.set_thumbnail(url=video_info.get('thumbnail_url'))
                    embedMsg.add_field(name="YouTube 頻道", value=channel_name, inline=False)
                    embedMsg.add_field(name="YouTube 曲名", value=video_title, inline=False)
                    embedMsg.add_field(name="曲目長度", value=video_length, inline=False)
                    embedMsg.set_footer(text=f"添加者：{added_by}")
                    await ctx.send(embed=embedMsg)
                else:
                    u_song += (ctx.author.id,)
                    if ctx.guild.id not in song_queue:
                        song_queue[ctx.guild.id] = [u_song]
                    else:
                        song_queue[ctx.guild.id].append(u_song)
                    embedMsg = discord.Embed(title="已添加進佇列",
                                            description=f"**[{u_song[1]}]({url})**",
                                            color=embed_color)
                    await ctx.send(embed=embedMsg)
                if not ctx.voice_client.is_playing():
                    self.check_queue_and_play_next_if_have_next(ctx)
            elif u_song is None:
                embedMsg = discord.Embed(description="不支援該平台", color=embed_color)
                await ctx.reply(embed=embedMsg)
            elif u_song == 0:
                embedMsg = discord.Embed(description="這不是正確的音樂連結", color=embed_color)
                await ctx.reply(embed=embedMsg)
            
    def find(self, url: str):
        if url.startswith(("https://streetvoice.com/", "http://streetvoice.com/")):
            s = url.split("/")
            s = list(filter(None, s))
            if s[-1].isnumeric and s[-2] == "songs":
                return self.streetvoice(s[-1]), self.streetvoice_title(s[-1]), url
        elif url.startswith(("https://www.youtube.com/watch?v=", "http://www.youtube.com/watch?v=")):
            s = self.yt(url)
            if s and s[0]:
                return s
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

    def yt(self, url):
        print(f"嘗試處理YouTube連結：{url}")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': '%(title)s.%(ext)s',
                'quiet': False,
                'force_generic_extractor': True,
                '--socket-timeout': '30',
            }
            ydl = YoutubeDL(ydl_opts)
            r = ydl.extract_info(url, download=False)
            if r and 'formats' in r and r['formats']:
                return r['formats'][0]['url'], r['title'], url
        except Exception as e:
            print(f"YouTube下載錯誤: {e}")
        return None
    
    def get_youtube_video_info(self, url):
        try:
            ydl_opts = {
                'quiet': True,
            }
            ydl = YoutubeDL(ydl_opts)
            r = ydl.extract_info(url, download=False)
            if r and 'uploader' in r and 'title' in r and 'duration' in r:
                return {
                    'channel_name': r['uploader'],
                    'video_title': r['title'],
                    'video_length': self.format_duration(r['duration']),
                    'thumbnail_url': r['thumbnail'],
                }
        except Exception as e:
            print(f"提取YouTube信息錯誤: {e}")
        return None
    
    def format_duration(self, seconds):
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes)} 分 {int(secs)} 秒"
    
    async def play_next(self, ctx):
        if self.queue:
            song_url = self.queue.pop(0)
            source = discord.FFmpegPCMAudio(song_url, **FFMPEG_OPTS)
            voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            try:
                voice.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            except Exception as e:
                print(f"播放下一首歌曲時出錯: {e}")
                await ctx.send("播放下一首歌曲時出錯。")
            # 類似上面的情況，考慮處理播放下一首歌曲時出現的錯誤，並調整佇列或通知使用者。

        else:
            await ctx.send("播放清單為空。離開語音頻道。")
            await self.leave_voice_channel(ctx)
                
    
    @commands.command(aliases=["LIST", "list"])
    async def List(self, ctx):
        if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
            queue_list = "\n".join([f"{index + 1}. [{song[1]}]({song[2]})" for index, song in enumerate(song_queue[ctx.guild.id])])
            embedMsg = discord.Embed(title="播放清單", description=queue_list, color=embed_color)
            await ctx.send(embed=embedMsg)
        else:
            embedMsg = discord.Embed(description="播放清單為空", color=embed_color)
            await ctx.send(embed=embedMsg)

async def setup(bot):
    await bot.add_cog(Music(bot))
    print("Music.py is ready")
