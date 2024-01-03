import discord
from discord.ext import commands
import requests
import youtube_dl
from youtube_dl import YoutubeDL
import asyncio
import time

embed_color = 0xf7bf25
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
            # 在這裡設定冷卻時間，這裡是 2 秒
            if ctx.command.name in ["play", "join", "leave", "list"]:
                return commands.cooldown(1, 2, commands.BucketType.guild)
        return True
        
    def check_queue_and_play_next_if_have_next(self, ctx: commands.Context):
        if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
            if now_playing.get(ctx.guild.id) != song_queue[ctx.guild.id][0]:
                voice = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
                u_song = song_queue[ctx.guild.id].pop(0)
                now_playing[ctx.guild.id] = u_song
                skip_vote[ctx.guild.id] = []
                voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS),
                        after=lambda e: self.check_queue_and_play_next_if_have_next(ctx))
                embedMsg = discord.Embed(title="正在播放",
                                        description=f"**[{u_song[1]}]({u_song[2]})**",
                                        color=embed_color)
                ctx.bot.loop.create_task(ctx.send(embed=embedMsg))
        else:
            now_playing[ctx.guild.id] = None
            skip_vote[ctx.guild.id] = []
            asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), ctx.bot.loop)
        
    async def send_message_with_retry(self, ctx, message_content):
        retry_count = 0
        while retry_count < 5:  # 最多重試 5 次
            try:
                await ctx.send(message_content)
                break  # 如果成功，退出循環
            except discord.HTTPException as e:
                if e.status == 429:  # 如果是速率限制，等待後重試
                    retry_after = e.retry_after
                    print(f"速率限制。{retry_after} 秒後重試。")
                    await asyncio.sleep(retry_after)
                    retry_count += 1
                else:
                    print(f"無法發送消息：{e}")
                    break  # 如果不是速率限制問題，退出循環
        
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
        if not ctx.author.voice:  # 使用者沒有在語音頻道內
            embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)
            return

        if ctx.voice_client is not None:  # 機器人有在語音頻道內但使用者頻道不同
            if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
                embedMsg = discord.Embed(description="你必須在相同的語音頻道才能使用此指令", color=embed_color)
                await ctx.reply(embed=embedMsg)
                return

        if not ctx.voice_client:  # 機器人沒在語音頻道內
            vc = ctx.author.voice.channel
            await vc.connect()

        if not ctx.voice_client.is_playing():
            await self.send_message_with_retry(ctx, "正在播放...")

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

                    embedMsg = discord.Embed(title="已添加整個播放清單進佇列", color=embed_color)
                    await ctx.send(embed=embedMsg)
                else:
                    embedMsg = discord.Embed(description="無法獲取播放清單的信息", color=embed_color)
                    await ctx.send(embed=embedMsg)
                    return
                # 檢查是否正在播放音樂，如果不是，則開始播放下一首歌曲
                if not ctx.voice_client.is_playing():
                    self.check_queue_and_play_next_if_have_next(ctx)

        # 如果是單個YouTube影片或其他支援的音樂平台
        else:
            u_song = self.find(url)
            if u_song is not None and u_song != 0 and u_song[0]:
                if ctx.guild.id not in song_queue or not song_queue[ctx.guild.id]:
                    now_playing[ctx.guild.id] = u_song
                    voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS),
                            after=lambda e: self.check_queue_and_play_next_if_have_next(ctx))
                    skip_vote[ctx.guild.id] = []
                    embedMsg = discord.Embed(title="正在播放",
                                            description=f"**[{u_song[1]}]({url})**",
                                            color=embed_color)
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
                # 檢查是否正在播放音樂，如果不是，則開始播放下一首歌曲
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
