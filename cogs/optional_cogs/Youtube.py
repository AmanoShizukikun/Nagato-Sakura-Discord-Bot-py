import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import datetime
import time
import asyncio
import functools

FFMPEG_OPTS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}  # 每個伺服器的語音連接
        self.song_queue = {}  # 每個伺服器的播放隊列
        self.now_playing = {}  # 每個伺服器當前播放的歌曲
        self.embed_color = 0xFF0000
        
        # 清理任務
        self.cleanup_task = None
        self.start_cleanup_task()

    def start_cleanup_task(self):
        """啟動清理任務"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self.periodic_cleanup())

    async def periodic_cleanup(self):
        """定期清理不活躍的伺服器資料"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小時清理一次
                
                # 清理不活躍的伺服器隊列
                inactive_guilds = []
                for guild_id in list(self.song_queue.keys()):
                    guild = self.bot.get_guild(guild_id)
                    if guild is None:  # 機器人已不在該伺服器
                        inactive_guilds.append(guild_id)
                
                for guild_id in inactive_guilds:
                    # 清理語音連接
                    voice_client = self.voice_clients.get(guild_id)
                    if voice_client and voice_client.is_connected():
                        await voice_client.disconnect()
                    
                    self.voice_clients.pop(guild_id, None)
                    self.song_queue.pop(guild_id, None)
                    self.now_playing.pop(guild_id, None)
                    print(f"清理了不活躍伺服器的資料: {guild_id}")
                    
            except Exception as e:
                print(f"清理任務錯誤: {e}")
                await asyncio.sleep(60)  # 出錯時等待1分鐘再重試

    def cog_unload(self):
        """Cog卸載時停止清理任務"""
        if self.cleanup_task:
            self.cleanup_task.cancel()

    async def disconnect_if_alone(self, guild_id):
        """如果語音頻道中只剩機器人，自動離開"""
        voice_client = self.voice_clients.get(guild_id)
        if voice_client and voice_client.is_connected():
            channel = voice_client.channel
            if len([member for member in channel.members if not member.bot]) == 0:
                # 只剩機器人，自動離開
                await voice_client.disconnect()
                self.voice_clients.pop(guild_id, None)
                self.song_queue.pop(guild_id, None)
                self.now_playing.pop(guild_id, None)
                return True
        return False

    def _get_user_voice_channel(self, ctx_or_interaction):
        """獲取用戶的語音頻道"""
        if isinstance(ctx_or_interaction, discord.Interaction):
            return ctx_or_interaction.user.voice.channel if ctx_or_interaction.user.voice else None
        else:
            return ctx_or_interaction.author.voice.channel if ctx_or_interaction.author.voice else None

    def _get_guild_id(self, ctx_or_interaction):
        """獲取伺服器ID"""
        return ctx_or_interaction.guild.id if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.guild_id

    async def join_voice_channel(self, ctx_or_interaction):
        voice_channel = self._get_user_voice_channel(ctx_or_interaction)
        guild_id = self._get_guild_id(ctx_or_interaction)

        if not voice_channel:
            error_msg = "請先加入一個語音頻道再使用長門櫻的音樂功能喔~"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(error_msg)
            else:
                await ctx_or_interaction.send(error_msg)
            return False

        voice_client = self.voice_clients.get(guild_id)

        if voice_client and voice_client.is_connected():
            if voice_client.channel == voice_channel:
                success_msg = "長門櫻已經在您的語音頻道中了~"
            else:
                await voice_client.move_to(voice_channel)
                success_msg = f"長門櫻已移動到 {voice_channel.name} 語音頻道"
        else:
            voice_client = await voice_channel.connect()
            self.voice_clients[guild_id] = voice_client
            success_msg = f"長門櫻已加入 {voice_channel.name} 語音頻道"

        if guild_id not in self.song_queue:
            self.song_queue[guild_id] = []
        if guild_id not in self.now_playing:
            self.now_playing[guild_id] = None

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(success_msg)
        else:
            await ctx_or_interaction.send(success_msg)
        return True

    async def leave_voice_channel(self, ctx_or_interaction):
        guild_id = self._get_guild_id(ctx_or_interaction)
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            self.voice_clients.pop(guild_id, None)
            self.song_queue.pop(guild_id, None)
            self.now_playing.pop(guild_id, None)
            # 清空當前伺服器的隊列，而不是全部
            if guild_id in self.song_queue:
                self.song_queue[guild_id].clear()
            
            success_msg = "長門櫻已離開語音頻道，感謝使用音樂服務~"
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(success_msg)
            elif isinstance(ctx_or_interaction, discord.Interaction):
                # 檢查是否已經回應過
                if ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.followup.send(success_msg)
                else:
                    await ctx_or_interaction.response.send_message(success_msg)
        else:
            error_msg = "長門櫻目前未加入任何語音頻道"
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(error_msg)
            else:
                await ctx_or_interaction.response.send_message(error_msg)
                
    async def play_join_voice_channel(self, ctx_or_interaction):
        """自動加入語音頻道用於播放"""
        voice_channel = self._get_user_voice_channel(ctx_or_interaction)
        guild_id = self._get_guild_id(ctx_or_interaction)
        
        if not voice_channel:
            return False

        voice_client = self.voice_clients.get(guild_id)
        
        if not voice_client or not voice_client.is_connected():
            voice_client = await voice_channel.connect()
            self.voice_clients[guild_id] = voice_client
            if guild_id not in self.song_queue:
                self.song_queue[guild_id] = []
            if guild_id not in self.now_playing:
                self.now_playing[guild_id] = None
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
        
        return True

    async def play_song(self, ctx_or_interaction, url):
        # 檢查用戶是否在語音頻道中
        if not self._get_user_voice_channel(ctx_or_interaction):
            error_msg = "請先加入一個語音頻道再使用長門櫻的音樂功能喔~"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(error_msg)
            else:
                await ctx_or_interaction.send(error_msg)
            return

        start_time = time.time()

        if not await self.play_join_voice_channel(ctx_or_interaction):
            error_msg = "無法加入語音頻道，請檢查長門櫻的權限設定"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(error_msg)
            else:
                await ctx_or_interaction.send(error_msg)
            return

        guild_id = self._get_guild_id(ctx_or_interaction)
        voice_client = self.voice_clients.get(guild_id)

        if voice_client and voice_client.is_connected():
            # 檢查是否為播放列表 URL
            is_playlist = any(keyword in url.lower() for keyword in ['playlist', 'list=', '&list='])
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
                'restrictfilenames': True,
                'ignoreerrors': True,  # 忽略單個視頻錯誤，繼續處理其他視頻
                'logtostderr': False,
                'socket_timeout': 30,
            }
            
            # 對於播放列表，限制數量並調整設定
            if is_playlist:
                ydl_opts.update({
                    'playlistend': 25,  # 限制最多50首歌
                    'extract_flat': False,  # 需要完整資訊用於播放
                })
                timeout = 90.0  # 播放列表使用90秒超時
                processing_msg = "🎵 正在處理播放列表，請稍候..."
            else:
                ydl_opts['noplaylist'] = True  # 單首歌曲不處理播放列表
                timeout = 30.0  # 單首歌曲30秒超時
                processing_msg = "🎵 正在處理歌曲，請稍候..."

            # 發送處理中訊息
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(processing_msg)
            else:
                process_msg = await ctx_or_interaction.send(processing_msg)

            try:
                loop = asyncio.get_event_loop()
                
                def extract_info(url, ydl_opts):
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(url, download=False)
                
                info = await asyncio.wait_for(
                    loop.run_in_executor(None, functools.partial(extract_info, url, ydl_opts)),
                    timeout=timeout
                )
                
                added_count = 0
                failed_count = 0
                
                if 'entries' in info:
                    # 播放列表處理
                    valid_entries = []
                    for entry in info['entries']:
                        if entry and entry.get('url'):  # 確保條目有效且有 URL
                            valid_entries.append(entry)
                        else:
                            failed_count += 1
                    
                    for entry in valid_entries:
                        self.song_queue[guild_id].append(entry)
                        added_count += 1
                    
                    end_time = time.time()
                    elapsed_time = round(end_time - start_time, 2)
                    
                    # 更新處理結果
                    result_msg = f"🎵 播放列表處理完成！\n"
                    result_msg += f"✅ 成功添加：{added_count} 首歌曲\n"
                    if failed_count > 0:
                        result_msg += f"❌ 跳過失效：{failed_count} 首歌曲\n"
                    result_msg += f"⏱️ 處理時間：{elapsed_time} 秒"
                    
                    if isinstance(ctx_or_interaction, discord.Interaction):
                        await ctx_or_interaction.edit_original_response(content=result_msg)
                    else:
                        await process_msg.edit(content=result_msg)
                else:
                    # 單首歌曲處理
                    if info and info.get('url'):
                        self.song_queue[guild_id].append(info)
                        added_count = 1
                        
                        if isinstance(ctx_or_interaction, discord.Interaction):
                            await ctx_or_interaction.edit_original_response(content="🎵 正在顯示歌曲資訊...")
                            await self.send_single_song_embed_followup(ctx_or_interaction, info, info['url'], info.get('channel', '未知頻道'), info['title'], info.get('duration', 0), str(ctx_or_interaction.user.display_name))
                        else:
                            await process_msg.delete()
                            await self.send_single_song_embed(ctx_or_interaction, info, info['url'], info.get('channel', '未知頻道'), info['title'], info.get('duration', 0), str(ctx_or_interaction.author))

                if added_count > 0 and not voice_client.is_playing():
                    await self.play_next(ctx_or_interaction)
                elif added_count == 0:
                    error_msg = "❌ 無法添加任何歌曲到播放列表"
                    if isinstance(ctx_or_interaction, discord.Interaction):
                        await ctx_or_interaction.edit_original_response(content=error_msg)
                    else:
                        await process_msg.edit(content=error_msg)
                    
            except asyncio.TimeoutError:
                error_msg = f"⏰ 處理超時！\n"
                if is_playlist:
                    error_msg += "播放列表太大或網路連接緩慢\n"
                    error_msg += "建議：嘗試較小的播放列表或單首歌曲"
                else:
                    error_msg += "請檢查網路連接或稍後再試"
                    
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.edit_original_response(content=error_msg)
                else:
                    await process_msg.edit(content=error_msg)
            except Exception as e:
                error_msg = f"❌ 處理時發生錯誤\n錯誤：{str(e)[:100]}..."
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.edit_original_response(content=error_msg)
                else:
                    await process_msg.edit(content=error_msg)

    async def play_next(self, ctx_or_interaction, retry_count=3):
        guild_id = self._get_guild_id(ctx_or_interaction)
        voice_client = self.voice_clients.get(guild_id)
        
        if not voice_client or not voice_client.is_connected():
            return
            
        # 等待當前歌曲播放完畢
        if voice_client.is_playing():
            while voice_client.is_playing():
                await asyncio.sleep(1)
        
        queue = self.song_queue.get(guild_id, [])
        
        if queue:
            song_info = queue.pop(0)
            self.now_playing[guild_id] = song_info
            
            try:
                source = discord.FFmpegPCMAudio(song_info['url'], **FFMPEG_OPTS)
                voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx_or_interaction)) if e is None else print(f"播放錯誤: {e}"))
                
                # 等待播放開始
                await asyncio.sleep(1)
                retries = 0
                while retries < retry_count:
                    if voice_client.is_playing():
                        break
                    retries += 1
                    await asyncio.sleep(1)
                    
                if retries == retry_count and not voice_client.is_playing():
                    error_msg = f"⚠️ 播放失敗，跳過：{song_info.get('title', '未知歌曲')}"
                    if isinstance(ctx_or_interaction, discord.Interaction):
                        try:
                            await ctx_or_interaction.followup.send(error_msg)
                        except:
                            pass
                    else:
                        try:
                            await ctx_or_interaction.send(error_msg)
                        except:
                            pass
                    await self.play_next(ctx_or_interaction)
                    
            except Exception as e:
                print(f"播放錯誤: {e}")
                error_msg = f"⚠️ 播放時發生錯誤，正在嘗試下一首..."
                if isinstance(ctx_or_interaction, discord.Interaction):
                    try:
                        await ctx_or_interaction.followup.send(error_msg)
                    except:
                        pass
                else:
                    try:
                        await ctx_or_interaction.send(error_msg)
                    except:
                        pass
                await self.play_next(ctx_or_interaction)
        else:
            # 播放完畢
            self.now_playing[guild_id] = None
            try:
                finish_msg = "🎵 播放清單已播放完畢！感謝使用長門櫻的音樂服務~"
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.followup.send(finish_msg)
                else:
                    await ctx_or_interaction.send(finish_msg)
            except:
                pass
            await self.leave_voice_channel(ctx_or_interaction)

    async def send_single_song_embed(self, ctx_or_interaction, video_info, url, channel_name, video_title, video_length, added_by):
        duration_str = str(datetime.timedelta(seconds=video_length)) if video_length else "未知"
        
        embedMsg = discord.Embed(
            title="🎵 已添加到播放清單",
            description=f"**[{video_title}]({url})**",
            color=self.embed_color
        )
        
        embedMsg.set_thumbnail(url=video_info.get('thumbnail'))
        embedMsg.add_field(name="📺 YouTube 頻道", value=channel_name, inline=True)
        embedMsg.add_field(name="⏱️ 歌曲長度", value=duration_str, inline=True)
        embedMsg.add_field(name="👤 添加者", value=added_by, inline=True)
        
        # 添加額外資訊
        if video_info.get('view_count'):
            embedMsg.add_field(name="👀 觀看次數", value=f"{video_info['view_count']:,}", inline=True)
        
        if video_info.get('upload_date'):
            try:
                upload_date = datetime.datetime.strptime(video_info['upload_date'], '%Y%m%d').strftime('%Y年%m月%d日')
                embedMsg.add_field(name="📅 上傳日期", value=upload_date, inline=True)
            except:
                pass
        
        # 顯示隊列位置
        guild_id = self._get_guild_id(ctx_or_interaction)
        queue_length = len(self.song_queue.get(guild_id, []))
        if queue_length > 1:
            embedMsg.add_field(name="📋 隊列位置", value=f"第 {queue_length} 首", inline=True)
        
        embedMsg.set_footer(text="🎶 長門櫻音樂服務")

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embedMsg)
        elif isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embedMsg)

    async def send_single_song_embed_followup(self, interaction, video_info, url, channel_name, video_title, video_length, added_by):
        """用於 followup 訊息的 embed 版本"""
        duration_str = str(datetime.timedelta(seconds=video_length)) if video_length else "未知"
        
        embedMsg = discord.Embed(
            title="🎵 已添加到播放清單",
            description=f"**[{video_title}]({url})**",
            color=self.embed_color
        )
        
        embedMsg.set_thumbnail(url=video_info.get('thumbnail'))
        embedMsg.add_field(name="📺 YouTube 頻道", value=channel_name, inline=True)
        embedMsg.add_field(name="⏱️ 歌曲長度", value=duration_str, inline=True)
        embedMsg.add_field(name="👤 添加者", value=added_by, inline=True)
        
        # 添加額外資訊
        if video_info.get('view_count'):
            embedMsg.add_field(name="👀 觀看次數", value=f"{video_info['view_count']:,}", inline=True)
        
        if video_info.get('upload_date'):
            try:
                upload_date = datetime.datetime.strptime(video_info['upload_date'], '%Y%m%d').strftime('%Y年%m月%d日')
                embedMsg.add_field(name="📅 上傳日期", value=upload_date, inline=True)
            except:
                pass
        
        # 顯示隊列位置
        guild_id = self._get_guild_id(interaction)
        queue_length = len(self.song_queue.get(guild_id, []))
        if queue_length > 1:
            embedMsg.add_field(name="📋 隊列位置", value=f"第 {queue_length} 首", inline=True)
        
        embedMsg.set_footer(text="🎶 長門櫻音樂服務")
        
        await interaction.followup.send(embed=embedMsg)

    @commands.command(aliases=["JOIN", "join"])
    async def Join(self, ctx):
        await self.join_voice_channel(ctx)

    @commands.command(aliases=["LEAVE", "leave"])
    async def Leave(self, ctx):
        await self.leave_voice_channel(ctx)

    async def search_and_play(self, ctx_or_interaction, query):
        """搜尋並播放歌曲"""
        # 檢查是否為URL
        if query.startswith(('http://', 'https://', 'www.')):
            await self.play_song(ctx_or_interaction, query)
            return

        # 搜尋歌曲
        search_query = f"ytsearch5:{query}"  # 搜尋前5個結果
        await self.play_song(ctx_or_interaction, search_query)

    @commands.command(aliases=["SEARCH", "search"])
    async def Search(self, ctx, *, query):
        """搜尋並顯示歌曲選項"""
        # 檢查用戶是否在語音頻道中
        if not self._get_user_voice_channel(ctx):
            await ctx.send("請先加入一個語音頻道再使用長門櫻的音樂功能喔~")
            return

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # 只提取基本資訊
            }
            
            loop = asyncio.get_event_loop()
            
            def search_videos(query):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch5:{query}", download=False)
            
            search_results = await asyncio.wait_for(
                loop.run_in_executor(None, functools.partial(search_videos, query)),
                timeout=15.0
            )
            
            if search_results and 'entries' in search_results:
                entries = [entry for entry in search_results['entries'] if entry][:5]
                
                if entries:
                    embed = discord.Embed(
                        title=f"🔍 搜尋結果：{query}",
                        description="請選擇要播放的歌曲 (1-5)，或輸入 `cancel` 取消",
                        color=self.embed_color
                    )
                    
                    for i, entry in enumerate(entries, 1):
                        title = entry.get('title', '未知標題')
                        duration = entry.get('duration')
                        duration_str = str(datetime.timedelta(seconds=duration)) if duration else "未知"
                        channel = entry.get('uploader', '未知頻道')
                        
                        embed.add_field(
                            name=f"{i}. {title[:50]}{'...' if len(title) > 50 else ''}",
                            value=f"📺 {channel} | ⏱️ {duration_str}",
                            inline=False
                        )
                    
                    await ctx.send(embed=embed)
                    
                    # 等待用戶選擇
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                        choice = msg.content.lower()
                        
                        if choice == 'cancel':
                            await ctx.send("🚫 搜尋已取消")
                            return
                        
                        try:
                            choice_num = int(choice)
                            if 1 <= choice_num <= len(entries):
                                selected = entries[choice_num - 1]
                                video_url = f"https://www.youtube.com/watch?v={selected['id']}"
                                await self.play_song(ctx, video_url)
                            else:
                                await ctx.send("❌ 請輸入有效的數字 (1-5)")
                        except ValueError:
                            await ctx.send("❌ 請輸入有效的數字 (1-5)")
                            
                    except asyncio.TimeoutError:
                        await ctx.send("⏰ 搜尋超時，已自動取消")
                        
                else:
                    await ctx.send(f"😔 找不到與 '{query}' 相關的歌曲")
            else:
                await ctx.send(f"😔 找不到與 '{query}' 相關的歌曲")
                
        except Exception as e:
            await ctx.send(f"❌ 搜尋時發生錯誤：{str(e)[:100]}...")

    @commands.command(aliases=["PLAY", "play"])
    async def Play(self, ctx, *, url):
        await self.search_and_play(ctx, url)

    @commands.command(aliases=["LIST", "list"])
    async def List(self, ctx):
        guild_id = self._get_guild_id(ctx)
        queue = self.song_queue.get(guild_id, [])
        now_playing = self.now_playing.get(guild_id)
        
        if queue or now_playing:
            embed = discord.Embed(title="🎵 目前的播放清單", color=self.embed_color)
            
            # 顯示正在播放的歌曲
            if now_playing:
                embed.add_field(
                    name="🎶 正在播放", 
                    value=f"**{now_playing.get('title', '未知歌曲')}**", 
                    inline=False
                )
            
            # 顯示隊列中的歌曲
            if queue:
                number_of_songs = min(len(queue), 10)  # 顯示最多10首
                queue_text = ""
                for index, info in enumerate(queue[:number_of_songs]):
                    duration = str(datetime.timedelta(seconds=info.get('duration', 0))) if info.get('duration') else "未知"
                    queue_text += f"`{index + 1}.` **{info.get('title', '未知歌曲')}** `[{duration}]`\n"
                
                embed.add_field(name="📋 播放隊列", value=queue_text, inline=False)
                
                if len(queue) > 10:
                    embed.set_footer(text=f"還有 {len(queue) - 10} 首歌曲未顯示...")
            else:
                embed.add_field(name="📋 播放隊列", value="隊列為空", inline=False)
                
            embed.set_footer(text=f"總計 {len(queue)} 首歌曲在隊列中")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🎵 播放清單", 
                description="目前沒有歌曲在播放清單中\n使用 `!play <URL或歌曲名稱>` 來添加歌曲", 
                color=self.embed_color
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=["SKIP", "skip"])
    async def Skip(self, ctx, amount: int = 1):
        guild_id = self._get_guild_id(ctx)
        queue = self.song_queue.get(guild_id, [])
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_playing():
            if amount > 1:
                # 跳過多首歌曲
                skip_count = min(amount - 1, len(queue))  # -1 因為包含當前播放的歌曲
                for _ in range(skip_count):
                    if queue:
                        queue.pop(0)
                await ctx.send(f"⏭️ 長門櫻已跳過 {amount} 首歌曲")
            else:
                await ctx.send("⏭️ 長門櫻正在跳過當前歌曲")
            
            voice_client.stop()  # 這會觸發 play_next
        else:
            await ctx.send("❌ 目前沒有歌曲在播放中")

    @commands.command(aliases=["PAUSE", "pause"])
    async def Pause(self, ctx):
        guild_id = self._get_guild_id(ctx)
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ 長門櫻已暫停播放")
        else:
            await ctx.send("❌ 目前沒有歌曲在播放中")

    @commands.command(aliases=["RESUME", "resume"])
    async def Resume(self, ctx):
        guild_id = self._get_guild_id(ctx)
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ 長門櫻已恢復播放")
        else:
            await ctx.send("❌ 目前沒有歌曲被暫停")

    @commands.command(aliases=["STOP", "stop"])
    async def Stop(self, ctx):
        guild_id = self._get_guild_id(ctx)
        voice_client = self.voice_clients.get(guild_id)
        
        if guild_id in self.song_queue:
            self.song_queue[guild_id].clear()
        
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("⏹️ 長門櫻已停止播放並清空播放清單")
        else:
            await ctx.send("❌ 目前沒有歌曲在播放中")

    @commands.command(aliases=["NOWPLAYING", "nowplaying", "np"])
    async def NowPlaying(self, ctx):
        guild_id = self._get_guild_id(ctx)
        now_playing = self.now_playing.get(guild_id)
        voice_client = self.voice_clients.get(guild_id)
        
        if now_playing and voice_client and voice_client.is_playing():
            duration = str(datetime.timedelta(seconds=now_playing.get('duration', 0))) if now_playing.get('duration') else "未知"
            embed = discord.Embed(
                title="🎶 正在播放",
                description=f"**[{now_playing.get('title', '未知歌曲')}]({now_playing.get('webpage_url', '')})**",
                color=self.embed_color
            )
            embed.add_field(name="📺 頻道", value=now_playing.get('channel', '未知頻道'), inline=True)
            embed.add_field(name="⏱️ 長度", value=duration, inline=True)
            embed.add_field(name="👀 觀看次數", value=f"{now_playing.get('view_count', 0):,}" if now_playing.get('view_count') else "未知", inline=True)
            
            if now_playing.get('thumbnail'):
                embed.set_thumbnail(url=now_playing['thumbnail'])
                
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ 目前沒有歌曲在播放中")

    @app_commands.command(name="join", description="!Join - 長門櫻進入語音聊天室")
    async def join(self, interaction: discord.Interaction):
        await self.join_voice_channel(interaction)

    @app_commands.command(name="leave", description="!Leave - 長門櫻離開語音聊天室")
    async def leave(self, interaction: discord.Interaction):
        await self.leave_voice_channel(interaction)

    @app_commands.command(name="play", description="播放音樂 - 可以是URL或搜尋關鍵字")
    async def play(self, interaction: discord.Interaction, query: str):
        await self.search_and_play(interaction, query)

    @app_commands.command(name="search", description="搜尋歌曲並選擇播放")
    async def search(self, interaction: discord.Interaction, query: str):
        """搜尋並顯示歌曲選項 (斜線命令版本)"""
        # 檢查用戶是否在語音頻道中
        if not self._get_user_voice_channel(interaction):
            await interaction.response.send_message("請先加入一個語音頻道再使用長門櫻的音樂功能喔~")
            return

        await interaction.response.defer()  # 延遲回應，因為搜尋可能需要時間

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            loop = asyncio.get_event_loop()
            
            def search_videos(query):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch5:{query}", download=False)
            
            search_results = await asyncio.wait_for(
                loop.run_in_executor(None, functools.partial(search_videos, query)),
                timeout=15.0
            )
            
            if search_results and 'entries' in search_results:
                entries = [entry for entry in search_results['entries'] if entry][:5]
                
                if entries:
                    embed = discord.Embed(
                        title=f"🔍 搜尋結果：{query}",
                        description="使用 `/play <歌曲名稱>` 來直接播放，或點擊下面的連結",
                        color=self.embed_color
                    )
                    
                    result_text = ""
                    for i, entry in enumerate(entries, 1):
                        title = entry.get('title', '未知標題')
                        duration = entry.get('duration')
                        duration_str = str(datetime.timedelta(seconds=duration)) if duration else "未知"
                        channel = entry.get('uploader', '未知頻道')
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        
                        result_text += f"`{i}.` **[{title[:40]}{'...' if len(title) > 40 else ''}]({video_url})**\n"
                        result_text += f"📺 {channel} | ⏱️ {duration_str}\n\n"
                    
                    embed.description = result_text
                    await interaction.followup.send(embed=embed)
                    
                else:
                    await interaction.followup.send(f"😔 找不到與 '{query}' 相關的歌曲")
            else:
                await interaction.followup.send(f"😔 找不到與 '{query}' 相關的歌曲")
                
        except Exception as e:
            await interaction.followup.send(f"❌ 搜尋時發生錯誤：{str(e)[:100]}...")

    @app_commands.command(name="list", description="!List - 長門櫻顯示播放清單")
    async def list(self, interaction: discord.Interaction):
        guild_id = self._get_guild_id(interaction)
        queue = self.song_queue.get(guild_id, [])
        now_playing = self.now_playing.get(guild_id)
        
        if queue or now_playing:
            embed = discord.Embed(title="🎵 目前的播放清單", color=self.embed_color)
            
            # 顯示正在播放的歌曲
            if now_playing:
                embed.add_field(
                    name="🎶 正在播放", 
                    value=f"**{now_playing.get('title', '未知歌曲')}**", 
                    inline=False
                )
            
            # 顯示隊列中的歌曲
            if queue:
                number_of_songs = min(len(queue), 10)  # 顯示最多10首
                queue_text = ""
                for index, info in enumerate(queue[:number_of_songs]):
                    duration = str(datetime.timedelta(seconds=info.get('duration', 0))) if info.get('duration') else "未知"
                    queue_text += f"`{index + 1}.` **{info.get('title', '未知歌曲')}** `[{duration}]`\n"
                
                embed.add_field(name="📋 播放隊列", value=queue_text, inline=False)
                
                if len(queue) > 10:
                    embed.set_footer(text=f"還有 {len(queue) - 10} 首歌曲未顯示...")
            else:
                embed.add_field(name="📋 播放隊列", value="隊列為空", inline=False)
                
            embed.set_footer(text=f"總計 {len(queue)} 首歌曲在隊列中")
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="🎵 播放清單", 
                description="目前沒有歌曲在播放清單中\n使用 `/play <URL或歌曲名稱>` 來添加歌曲", 
                color=self.embed_color
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip", description="跳過當前歌曲或指定數量的歌曲")
    async def skip(self, interaction: discord.Interaction, amount: int = 1):
        guild_id = self._get_guild_id(interaction)
        queue = self.song_queue.get(guild_id, [])
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_playing():
            if amount > 1:
                skip_count = min(amount - 1, len(queue))
                for _ in range(skip_count):
                    if queue:
                        queue.pop(0)
                await interaction.response.send_message(f"⏭️ 長門櫻已跳過 {amount} 首歌曲")
            else:
                await interaction.response.send_message("⏭️ 長門櫻正在跳過當前歌曲")
            
            voice_client.stop()
        else:
            await interaction.response.send_message("❌ 目前沒有歌曲在播放中")

    @app_commands.command(name="pause", description="暫停當前播放的歌曲")
    async def pause(self, interaction: discord.Interaction):
        guild_id = self._get_guild_id(interaction)
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ 長門櫻已暫停播放")
        else:
            await interaction.response.send_message("❌ 目前沒有歌曲在播放中")

    @app_commands.command(name="resume", description="恢復播放暫停的歌曲")
    async def resume(self, interaction: discord.Interaction):
        guild_id = self._get_guild_id(interaction)
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ 長門櫻已恢復播放")
        else:
            await interaction.response.send_message("❌ 目前沒有歌曲被暫停")

    @app_commands.command(name="stop", description="停止播放並清空播放清單")
    async def stop(self, interaction: discord.Interaction):
        guild_id = self._get_guild_id(interaction)
        voice_client = self.voice_clients.get(guild_id)
        
        if guild_id in self.song_queue:
            self.song_queue[guild_id].clear()
        
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏹️ 長門櫻已停止播放並清空播放清單")
        else:
            await interaction.response.send_message("❌ 目前沒有歌曲在播放中")

    @app_commands.command(name="nowplaying", description="顯示當前播放的歌曲資訊")
    async def nowplaying(self, interaction: discord.Interaction):
        guild_id = self._get_guild_id(interaction)
        now_playing = self.now_playing.get(guild_id)
        voice_client = self.voice_clients.get(guild_id)
        
        if now_playing and voice_client and voice_client.is_playing():
            duration = str(datetime.timedelta(seconds=now_playing.get('duration', 0))) if now_playing.get('duration') else "未知"
            embed = discord.Embed(
                title="🎶 正在播放",
                description=f"**[{now_playing.get('title', '未知歌曲')}]({now_playing.get('webpage_url', '')})**",
                color=self.embed_color
            )
            embed.add_field(name="📺 頻道", value=now_playing.get('channel', '未知頻道'), inline=True)
            embed.add_field(name="⏱️ 長度", value=duration, inline=True)
            embed.add_field(name="👀 觀看次數", value=f"{now_playing.get('view_count', 0):,}" if now_playing.get('view_count') else "未知", inline=True)
            
            if now_playing.get('thumbnail'):
                embed.set_thumbnail(url=now_playing['thumbnail'])
                
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ 目前沒有歌曲在播放中")

async def setup(bot: commands.Bot):
    await bot.add_cog(Youtube(bot))
    print("Youtube.py is ready")
