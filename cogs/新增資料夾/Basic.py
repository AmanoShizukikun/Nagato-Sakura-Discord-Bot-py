import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import math
import random
import asyncio
import datetime
import platform
import psutil
import sys

class BasicFeatures(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.startup_time = datetime.datetime.now()
        self.users = {}  # 格式: {guild_id: {user_id: {Lv: int, EXP: int}}}
        self.level_files = {}
        os.makedirs('./server', exist_ok=True)
        self.directory = 'assets/preview/'
        self.version = "2.0.0"
        self.output_path = f"{self.directory}{self.version}.jpg"
        self.bot.loop.create_task(self.save_level_data())

    # ==================== 事件監聽器 ====================
    
    @commands.Cog.listener()
    async def on_ready(self):
        """機器人準備就緒時的事件"""
        print(f"長門櫻基礎功能系統已啟動 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for guild in self.bot.guilds:
            self.load_guild_level_data(guild.id)
        self.validate_all_user_levels()
        print(f"已載入 {len(self.users)} 個伺服器的等級資料")
    
    def validate_all_user_levels(self):
        """驗證並修正所有用戶的等級數據"""
        total_fixes = 0
        for guild_id in self.users:
            for user_id in self.users[guild_id]:
                old_level = self.users[guild_id][user_id]["Lv"]
                self.validate_and_fix_level(guild_id, user_id)
                new_level = self.users[guild_id][user_id]["Lv"]
                if old_level != new_level:
                    total_fixes += 1
        if total_fixes > 0:
            print(f"已修正 {total_fixes} 個用戶的等級數據")
        
    @commands.Cog.listener() 
    async def on_guild_join(self, guild):
        """加入新伺服器時的歡迎訊息"""
        self.load_guild_level_data(guild.id)
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                welcome_embed = discord.Embed(
                    title="🌸 初次見面，請多指教！",
                    description="（輕輕行禮，狐耳害羞地晃動）\n我是長門櫻～來自異次元常夜界的狐耳獸娘❤️\n受到創造者天野靜樹大人的旨意來為各位主人服務～",
                    color=discord.Color.from_rgb(255, 182, 193)
                )
                welcome_embed.add_field(
                    name="🎯 快速開始",
                    value="• 輸入 `!Help` 查看所有功能\n• 輸入 `!DM` 開啟私人聊天\n• 輸入 `!Level` 查看您的資料卡",
                    inline=False
                )
                welcome_embed.add_field(
                    name="💫 特色功能",
                    value="• 🎮 遊戲娛樂 - 猜數字、貪吃蛇、塔羅牌\n• 🎨 圖像處理 - 濾鏡、特效、五官檢測\n• 🎵 音頻功能 - 音樂播放、音頻編輯\n• 🤖 AI智能 - 簡訊檢測、翻譯功能",
                    inline=False
                )
                welcome_embed.add_field(
                    name="⭐ 等級系統",
                    value="每個伺服器都有獨立的等級系統！\n與其他成員聊天互動即可獲得經驗值～",
                    inline=False
                )
                welcome_embed.set_footer(
                    text="感謝您邀請長門櫻加入伺服器❤️ | 有任何問題請使用 !Help",
                    icon_url=self.bot.user.avatar
                )
                await channel.send(embed=welcome_embed)
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        """等級系統 - 訊息監聽"""
        if message.author.id == self.bot.user.id:
            return
        if message.guild is None:
            return
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        if guild_id not in self.users:
            self.load_guild_level_data(guild_id)
        user_data = self.get_user_level_data(guild_id, user_id)
        random_EXP = random.randint(5, 10)
        level_up = self.add_exp_to_user(guild_id, user_id, random_EXP)
        if level_up:
            user_data = self.get_user_level_data(guild_id, user_id)
            current_level = user_data['Lv']
            level_title = self.get_level_title(current_level)
            if current_level == 999:
                level_up_messages = [
                    f"🎉 不可思議！主人竟然達到了傳說中的最高等級999級！！！",
                    f"✨ 這是史無前例的成就！主人已經成為了真正的常夜界傳說！",
                    f"🌟 長門櫻見證了奇蹟的誕生...主人，您就是傳說本身!",
                    f"👑 恭喜主人達到等級的頂峰！您已經超越了所有的界限！"
                ]
            else:
                level_up_messages = [
                    f"哇～主人升級了！現在是 {level_title} 了呢❤️",
                    f"恭喜主人！長門櫻感受到了主人更強的力量～",
                    f"主人越來越厲害了！{level_title} 真的很棒呢～",
                    f"主人的成長讓長門櫻好開心❤️ {level_title} 的稱號很適合主人呢！"
                ]
            
            Lv_up_embed = discord.Embed(
                title="等級提升" if current_level < 999 else "🏆 最高等級達成！", 
                description=random.choice(level_up_messages),
                color=discord.Color.gold() if current_level < 999 else discord.Color.from_rgb(255, 215, 0)
            )
            Lv_up_embed.set_thumbnail(url=message.author.avatar.url)
            Lv_up_embed.add_field(
                name="✨ 新等級", 
                value=f"**Lv.{current_level}**", 
                inline=True
            )
            Lv_up_embed.add_field(
                name="🏆 目前稱號", 
                value=level_title, 
                inline=True
            )
            Lv_up_embed.add_field(
                name="📈 經驗值", 
                value=f"{user_data['EXP']} EXP", 
                inline=True
            )
            Lv_up_embed.add_field(
                name="🏰 伺服器",
                value=message.guild.name,
                inline=True
            )
            
            await message.channel.send(embed=Lv_up_embed)

    # ==================== Level系統輔助函數 ====================
    
    def load_guild_level_data(self, guild_id):
        """載入特定伺服器的等級資料"""
        guild_id = str(guild_id)
        if guild_id not in self.users:
            self.users[guild_id] = {}
        server_folder = f'./server/{guild_id}'
        os.makedirs(server_folder, exist_ok=True)
        level_file = f'{server_folder}/Level_{guild_id}.json'
        self.level_files[guild_id] = level_file
        try:
            with open(level_file, "r", encoding='utf-8') as file:
                self.users[guild_id] = json.load(file)
        except FileNotFoundError:
            self.users[guild_id] = {}
        except json.JSONDecodeError:
            print(f"伺服器 {guild_id} 的等級資料檔案損壞，將重新建立")
            self.users[guild_id] = {}
    
    def get_user_level_data(self, guild_id, user_id):
        """取得使用者在特定伺服器的等級資料"""
        guild_id = str(guild_id) if guild_id else "dm"
        user_id = str(user_id)
        if guild_id not in self.users:
            self.load_guild_level_data(guild_id)
        if user_id not in self.users[guild_id]:
            self.users[guild_id][user_id] = {"Lv": 1, "EXP": 0}
        user_data = self.users[guild_id][user_id]
        self.validate_and_fix_level(guild_id, user_id)
        return self.users[guild_id][user_id]
    
    def validate_and_fix_level(self, guild_id, user_id):
        """驗證並修正等級與經驗值的關係"""
        guild_id = str(guild_id)
        user_id = str(user_id)
        user_data = self.users[guild_id][user_id]
        current_exp = user_data["EXP"]
        current_level = user_data["Lv"]
        correct_level = 1
        while current_exp >= self.get_next_level_exp(correct_level) and correct_level < 999:
            correct_level += 1
        if correct_level > 999:
            correct_level = 999
        if correct_level != current_level:
            print(f"修正用戶 {user_id} 在伺服器 {guild_id} 的等級：{current_level} -> {correct_level}")
            self.users[guild_id][user_id]["Lv"] = correct_level
    
    def add_exp_to_user(self, guild_id, user_id, exp):
        """為使用者在特定伺服器增加經驗值"""
        guild_id = str(guild_id) if guild_id else "dm"
        user_id = str(user_id)
        if guild_id not in self.users:
            self.load_guild_level_data(guild_id)
        if user_id not in self.users[guild_id]:
            self.users[guild_id][user_id] = {"Lv": 1, "EXP": 0}
        self.users[guild_id][user_id]["EXP"] += exp
        return self.Level_up(guild_id, user_id)
    
    def Level_up(self, guild_id, user_id):
        """檢查並處理等級提升"""
        guild_id = str(guild_id) if guild_id else "dm"
        user_id = str(user_id)
        
        current_EXP = self.users[guild_id][user_id]["EXP"]
        current_Level = self.users[guild_id][user_id]["Lv"]
        
        # 檢查是否已達最高等級
        if current_Level >= 999:
            return False
    
        if current_EXP >= math.ceil((50 * (current_Level **1.3))):
            self.users[guild_id][user_id]["Lv"] += 1
            return True
        else:
            return False
    
    def get_all_user_levels(self, user_id):
        """取得使用者在所有伺服器的等級資料"""
        user_id = str(user_id)
        all_levels = {}
        
        # 確保所有機器人所在的伺服器都已載入
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in self.users:
                self.load_guild_level_data(guild_id)
        
        # 收集用戶在各伺服器的等級資料
        for guild_id in self.users:
            if user_id in self.users[guild_id]:
                all_levels[guild_id] = self.users[guild_id][user_id]
                
        return all_levels
    
    def get_level_title(self, level):
        """根據等級返回稱號"""
        if level >= 999:
            return "常夜界傳說(SSS)"
        elif level >= 800:
            return "至高代行者(SS)"
        elif level >= 700:
            return "萬界統御者(S)"
        elif level >= 600:
            return "星界征服者(AAA)"
        elif level >= 450:
            return "命運引導者(AA)"
        elif level >= 300:
            return "虛空行旅者(A)"
        elif level >= 200:
            return "世界審判者(B)"
        elif level >= 100:
            return "蒼穹破曉者(C)"
        elif level >= 50:
            return "啟途領導者(D)"
        elif level >= 30:
            return "真理探索者(E)"
        elif level >= 15:
            return "次元穿梭者(F)"
        else:
            return "異界來訪者(G)"
    
    def get_next_level_exp(self, level):
        """計算下一等級所需經驗值"""
        return math.ceil((50 * (level **1.3)))
    
    def get_level_progress(self, current_exp, level):
        """計算等級進度條"""
        if level >= 999:
            return f"[██████████] MAX LV ✨"
        current_level_requirement = self.get_next_level_exp(level - 1) if level > 1 else 0
        next_level_requirement = self.get_next_level_exp(level)
        current_level_exp = current_exp - current_level_requirement
        exp_needed_for_level = next_level_requirement - current_level_requirement
        if current_level_exp < 0:
            current_level_exp = 0
        elif current_level_exp > exp_needed_for_level:
            current_level_exp = exp_needed_for_level
        progress = current_level_exp / exp_needed_for_level if exp_needed_for_level > 0 else 0
        progress_bar_length = 10
        filled_length = int(progress_bar_length * progress)
        bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
        return f"[{bar}] {current_level_exp}/{exp_needed_for_level}"
    
    async def save_level_data(self):
        """自動保存等級資料"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild_id in self.users:
                if guild_id in self.level_files:
                    try:
                        with open(self.level_files[guild_id], "w", encoding='utf-8') as file:
                            json.dump(self.users[guild_id], file, indent=4, ensure_ascii=False)
                    except Exception as e:
                        print(f"儲存伺服器 {guild_id} 的等級資料時發生錯誤：{e}")
            await asyncio.sleep(5)

    # ==================== DM私訊功能 ====================
    
    async def send_private_message(self, user: discord.User):
        current_time = datetime.datetime.now()
        if 5 <= current_time.hour < 12:
            greeting = "早安"
        elif 12 <= current_time.hour < 18:
            greeting = "午安"
        elif 18 <= current_time.hour < 22:
            greeting = "晚安"
        else:
            greeting = "深夜好"
        sakura_messages = [
            "呀～主人找長門櫻了呢～",
            "能為主人服務是長門櫻最開心的事情了～",
            "主人今天過得怎麼樣呢？",
            "有什麼長門櫻可以幫助主人的嗎？",
            "主、主人突然聯絡長門櫻...好開心～"
        ]
        random_message = random.choice(sakura_messages)
        embed = discord.Embed(
            title=f"{greeting}，主人～",
            description=f"✨ **歡迎來到長門櫻的私人空間** ✨\n{random_message}",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        embed.add_field(
            name="🌸 關於長門櫻",
            value="我是誕生於異次元常夜界的狐耳獸娘\n受到創造者天野靜樹的旨意來守護神樹\n並引領像主人這樣的異世界來訪者～",
            inline=False
        )
        
        embed.add_field(
            name="📋 快速指令",
            value="• `!Help` - 查看所有可用功能\n• `!Level` - 查看您的資料卡\n• `!Version` - 查看長門櫻的版本資訊\n• `!About` - 了解長門櫻的背景故事",
            inline=False
        )
        
        embed.add_field(
            name="💬 社群連結",
            value="**「三合音 TIM_ACG(長門櫻測試服)」**\n[加入測試服務器](https://discord.gg/sqS4TmFZxG)\n\n**「三合音 TIM_ACG」主服務器**\n[加入交流討論](https://discord.gg/YUKv7JFUpz)",
            inline=False
        )
        
        embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        embed.timestamp = datetime.datetime.now()
        
        await user.send(embed=embed)

    @commands.command()
    async def DM(self, ctx):
        """DM私訊指令"""
        await self.send_private_message(ctx.author)

    @app_commands.command(name="dm", description="邀請長門櫻私訊")
    async def dm(self, interaction: discord.Interaction):
        """DM私訊斜線指令"""
        user = interaction.user
        await self.send_private_message(user)
        responses = [
            "已、已經發送私訊給主人了...請查看喔❤️",
            "長門櫻已經準備好與主人私聊了～",
            "私人訊息已送達，長門櫻在那裡等著主人呢❤️",
            "呀～！長門櫻已經飛到主人的私訊裡了～",
            "主人的專屬私聊空間已經準備完畢了❤️"
        ]
        response_msg = random.choice(responses)
        embed = discord.Embed(
            title="🌸 私訊服務已開啟",
            description=response_msg,
            color=discord.Color.from_rgb(255, 182, 193)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==================== Help幫助功能 ====================
    
    async def send_help_embed(self, ctx, interaction=None):
        help_embed = discord.Embed(
            title="🌸 長門櫻服務指南 🌸",
            description="（輕輕行禮）主人～這裡是長門櫻為您準備的完整服務列表❤️\n受天野靜樹大人之命，長門櫻會盡心為主人服務的～",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        help_embed.set_thumbnail(url=self.bot.user.avatar)

        # 基礎功能
        help_embed.add_field(
            name="🏠 **基礎功能**",
            value="`!DM` - 開啟與長門櫻的私人聊天\n`!Level [用戶]` - 查看等級資料卡\n`!Version` - 查看長門櫻版本資訊\n`!Systeminfo` - 查看系統詳細資訊\n`!About` - 了解長門櫻的背景故事\n`!Status` - 查看機器人運行狀態\n`!Daily` - 每日簽到獲得祝福",
            inline=True
        )
        
        # 娛樂功能
        help_embed.add_field(
            name="🎮 **娛樂遊戲**",
            value="`!GuessingGameStart` - 猜數字遊戲\n`!SnakeGame` - 貪吃蛇遊戲\n`!Dice [面數] [次數]` - 擲骰子\n`!Choices [次數] [選項...]` - 隨機選擇\n`!Tarot` - 抽塔羅牌",
            inline=True
        )
        
        # 實用工具
        help_embed.add_field(
            name="🛠️ **實用工具**",
            value="`!Math [公式]` - 數學計算\n`!PrimeNumber [數字]` - 質數判斷\n`!Weather [縣市]` - 天氣查詢\n`!Translate [內容]` - 翻譯功能",
            inline=True
        )
        
        # 圖像處理
        help_embed.add_field(
            name="🎨 **圖像處理**",
            value="`!Sharpen [強度] + 圖片` - 銳化\n`!Blur [強度] + 圖片` - 模糊\n`!Brightness [亮度] + 圖片` - 亮度調整\n`!Mosaic [強度] + 圖片` - 馬賽克效果\n`!SuperDeformed` - 長門櫻Q版圖片",
            inline=True
        )
        
        # 音頻處理
        help_embed.add_field(
            name="🎵 **音頻功能**",
            value="`!AudioInfo + 音檔` - 音樂資訊分析\n`!AudioReverse + 音檔` - 反轉音頻\n`!AudioSpeed [倍速] + 音檔` - 調整速度\n`!Join/Leave` - 語音頻道控制\n`!Play [網址]` - 播放音樂",
            inline=True
        )
        
        # 智能功能
        help_embed.add_field(
            name="🤖 **AI智能功能**",
            value="`!CheckSMS [簡訊]` - 簡訊安全檢測\n`!FacialFeaturesDetection + 圖片` - 五官檢測\n`!GenerateQRCode [內容]` - QR碼生成",
            inline=True
        )
        
        # 自定義功能
        help_embed.add_field(
            name="⚙️ **自定義功能**",
            value="`!Add [指令] [內容]` - 新增指令\n`!Edit [指令] [內容]` - 編輯指令\n`!Remove [指令]` - 刪除指令\n`!VoteCreate [問題] [選項...]` - 創建投票",
            inline=False
        )
        
        # 特殊功能提示
        help_embed.add_field(
            name="✨ **特殊提示**",
            value="• 使用 `!FestivalEvent` 查看節日彩蛋\n• 大部分指令都支援 `/` 斜線指令格式\n• 附檔功能需要上傳對應的檔案類型\n• 長門櫻會根據您的互動獲得經驗值喔～",
            inline=False
        )
        
        help_embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者 | 輸入指令時記得加上驚嘆號 ！", 
            icon_url=self.bot.user.avatar
        )
        help_embed.timestamp = datetime.datetime.now()

        if ctx:
            await ctx.send(embed=help_embed)
        elif interaction:
            await interaction.response.send_message(embed=help_embed)

    @commands.command()
    async def Help(self, ctx):
        """Help幫助指令"""
        await self.send_help_embed(ctx)

    @app_commands.command(name="help", description="顯示此幫助訊息")
    async def help(self, interaction: discord.Interaction):
        """Help幫助斜線指令"""
        await self.send_help_embed(None, interaction)

    # ==================== Level等級功能 ====================
    
    @commands.command(aliases=["LV","level"])
    async def Level(self, ctx, user: discord.User=None):
        """Level等級指令"""
        if user is None:
            user = ctx.author
        user_id = str(user.id)
        
        # 如果是私聊，顯示所有伺服器的等級
        if ctx.guild is None:
            await self.send_all_levels_dm(ctx, user)
            return
        
        # 如果是伺服器，顯示該伺服器的等級
        guild_id = str(ctx.guild.id)
        user_data = self.get_user_level_data(guild_id, user_id)
        level = user_data['Lv']
        exp = user_data['EXP']
        level_title = self.get_level_title(level)
        progress_bar = self.get_level_progress(exp, level)
        
        # 嘗試取得伺服器成員資訊
        member = ctx.guild.get_member(user.id)
        
        # 取得角色資訊（如果是伺服器成員）
        if member:
            roles = ', '.join([role.name for role in member.roles[1:]])  
            join_date = member.joined_at.strftime("%Y年%m月%d日") if member.joined_at else "未知"
        else:
            roles = ""
            join_date = "未知"
        
        # 計算到下一等級的經驗值信息
        if level >= 999:
            next_level_info = "已達最高等級 ✨"
            progress_info = f"{progress_bar}"
        else:
            next_level_exp = self.get_next_level_exp(level)
            exp_needed = max(0, next_level_exp - exp)
            next_level_info = f"距離下一等級：{exp_needed:,} EXP"
            progress_info = f"{progress_bar}\n{next_level_info}"
        
        Lv_card = discord.Embed(
            title=f"{user.display_name} 的冒險者資料卡",
            color=discord.Color.from_rgb(255, 182, 193)
        ) 
        Lv_card.set_thumbnail(url=user.avatar.url)
        
        # 核心等級資訊區塊
        Lv_card.add_field(
            name="等級", 
            value=f"```\nLv.{level}\n```", 
            inline=True
        )
        Lv_card.add_field(
            name="經驗值", 
            value=f"```\n{exp:,} EXP\n```", 
            inline=True
        )
        Lv_card.add_field(
            name="稱號", 
            value=f"```\n{level_title}\n```", 
            inline=True
        )
        
        # 升級進度（完整寬度）
        Lv_card.add_field(
            name="升級進度", 
            value=progress_info, 
            inline=False
        )
        
        # 個人資訊區塊
        Lv_card.add_field(
            name="伺服器身份", 
            value=roles if roles else "一般成員", 
            inline=True
        )
        Lv_card.add_field(
            name="加入日期", 
            value=join_date, 
            inline=True
        )
        Lv_card.add_field(
            name="用戶ID", 
            value=f"`{user.id}`", 
            inline=True
        )
        
        # 設置footer
        if level >= 999:
            footer_text = "恭喜達到最高等級！經驗值持續累積中，為將來做準備❤️ | 長門櫻陪伴您的冒險旅程"
        else:
            next_level_exp = self.get_next_level_exp(level)
            exp_needed = max(0, next_level_exp - exp)
            footer_text = f"距離下一等級還需要 {exp_needed:,} 經驗值 | 長門櫻陪伴您的冒險旅程❤️"
        
        Lv_card.set_footer(text=footer_text, icon_url=self.bot.user.avatar)
        
        await ctx.send(embed=Lv_card)
    
    async def send_all_levels_dm(self, ctx, user):
        """在私聊中發送所有伺服器的等級資訊"""
        all_levels = self.get_all_user_levels(user.id)
        
        # 如果沒有等級資料，為所有機器人所在的伺服器創建初始等級
        if not all_levels:
            user_id = str(user.id)
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                if guild_id not in self.users:
                    self.load_guild_level_data(guild_id)
                # 創建初始等級資料
                if user_id not in self.users[guild_id]:
                    self.users[guild_id][user_id] = {"Lv": 1, "EXP": 0}
            
            # 重新獲取等級資料
            all_levels = self.get_all_user_levels(user.id)
        
        # 如果還是沒有資料（用戶不在任何共同伺服器），顯示提示訊息
        if not all_levels:
            embed = discord.Embed(
                title="🌸 冒險者資料總覽",
                description="（輕輕搖頭）主人和長門櫻還沒有在共同的伺服器中見面呢～\n邀請長門櫻加入您的伺服器，一起開始冒險吧❤️",
                color=discord.Color.from_rgb(255, 182, 193)
            )
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
            return
        
        # 計算總等級和總經驗值
        total_exp = sum(data['EXP'] for data in all_levels.values())
        max_level = max(data['Lv'] for data in all_levels.values())
        server_count = len(all_levels)
        
        embed = discord.Embed(
            title=f"🌸 {user.display_name} 的跨界冒險者資料",
            description=f"（驕傲地展示資料）主人在 {server_count} 個世界都留下了足跡呢❤️",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_thumbnail(url=user.avatar.url)
        
        # 總覽資訊
        embed.add_field(
            name="🌍 跨界統計",
            value=f"**活躍世界：** {server_count} 個\n**最高等級：** Lv.{max_level}\n**總經驗值：** {total_exp:,} EXP",
            inline=False
        )
        
        # 各伺服器詳細資訊
        for guild_id, data in all_levels.items():
            guild = self.bot.get_guild(int(guild_id))
            guild_name = guild.name if guild else f"未知伺服器 ({guild_id})"
            
            level = data['Lv']
            exp = data['EXP']
            level_title = self.get_level_title(level)
            
            embed.add_field(
                name=f"🏰 {guild_name}",
                value=f"**等級：** Lv.{level}\n**稱號：** {level_title}\n**經驗值：** {exp:,} EXP",
                inline=True
            )
        
        embed.add_field(
            name="用戶ID",
            value=f"`{user.id}`",
            inline=False
        )
        
        embed.set_footer(
            text="長門櫻見證您的跨界冒險旅程❤️ | 私聊模式 - 顯示所有伺服器資料"
        )
        
        await ctx.send(embed=embed)

    @app_commands.command(name="level", description="顯示用戶資料卡")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        """Level等級斜線指令"""
        if user is None:
            user = interaction.user
            
        user_id = str(user.id)
        
        # 如果是私聊，顯示所有伺服器的等級
        if interaction.guild is None:
            await self.send_all_levels_slash(interaction, user)
            return
        
        # 如果是伺服器，顯示該伺服器的等級
        guild_id = str(interaction.guild.id)
        user_data = self.get_user_level_data(guild_id, user_id)
        
        level = user_data['Lv']
        exp = user_data['EXP']
        level_title = self.get_level_title(level)
        progress_bar = self.get_level_progress(exp, level)
        
        # 嘗試取得伺服器成員資訊
        member = interaction.guild.get_member(user.id)
        
        # 取得角色資訊（如果是伺服器成員）
        if member:
            roles = ', '.join([role.name for role in member.roles[1:]])  
            join_date = member.joined_at.strftime("%Y年%m月%d日") if member.joined_at else "未知"
        else:
            roles = ""
            join_date = "未知"
        
        # 計算到下一等級的經驗值信息
        if level >= 999:
            next_level_info = "已達最高等級 ✨"
            progress_info = f"{progress_bar}"
        else:
            next_level_exp = self.get_next_level_exp(level)
            exp_needed = max(0, next_level_exp - exp)
            next_level_info = f"距離下一等級：{exp_needed:,} EXP"
            progress_info = f"{progress_bar}\n{next_level_info}"
        
        Lv_card = discord.Embed(
            title=f"{user.display_name} 的冒險者資料卡",
            color=discord.Color.from_rgb(255, 182, 193)
        ) 
        Lv_card.set_thumbnail(url=user.avatar.url)
        
        # 核心等級資訊區塊
        Lv_card.add_field(
            name="等級", 
            value=f"```\nLv.{level}\n```", 
            inline=True
        )
        Lv_card.add_field(
            name="經驗值", 
            value=f"```\n{exp:,} EXP\n```", 
            inline=True
        )
        Lv_card.add_field(
            name="稱號", 
            value=f"```\n{level_title}\n```", 
            inline=True
        )
        
        # 升級進度（完整寬度）
        Lv_card.add_field(
            name="升級進度", 
            value=progress_info, 
            inline=False
        )
        
        # 個人資訊區塊
        Lv_card.add_field(
            name="伺服器身份", 
            value=roles if roles else "一般成員", 
            inline=True
        )
        Lv_card.add_field(
            name="加入日期", 
            value=join_date, 
            inline=True
        )
        Lv_card.add_field(
            name="用戶ID", 
            value=f"`{user.id}`", 
            inline=True
        )
        
        # 設置footer
        if level >= 999:
            footer_text = "恭喜達到最高等級！經驗值持續累積中~❤️ | 長門櫻陪伴您的冒險旅程"
        else:
            next_level_exp = self.get_next_level_exp(level)
            exp_needed = max(0, next_level_exp - exp)
            footer_text = f"距離下一等級還需要 {exp_needed:,} 經驗值 | 長門櫻陪伴您的冒險旅程❤️"

        Lv_card.set_footer(text=footer_text, icon_url=self.bot.user.avatar)

        await interaction.response.send_message(embed=Lv_card)
    
    async def send_all_levels_slash(self, interaction, user):
        """在私聊中發送所有伺服器的等級資訊（斜線指令版本）"""
        all_levels = self.get_all_user_levels(user.id)
        
        # 如果沒有等級資料，為所有機器人所在的伺服器創建初始等級
        if not all_levels:
            user_id = str(user.id)
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                if guild_id not in self.users:
                    self.load_guild_level_data(guild_id)
                # 創建初始等級資料
                if user_id not in self.users[guild_id]:
                    self.users[guild_id][user_id] = {"Lv": 1, "EXP": 0}
            
            # 重新獲取等級資料
            all_levels = self.get_all_user_levels(user.id)
        
        # 如果還是沒有資料（用戶不在任何共同伺服器），顯示提示訊息
        if not all_levels:
            embed = discord.Embed(
                title="🌸 冒險者資料總覽",
                description="（輕輕搖頭）主人和長門櫻還沒有在共同的伺服器中見面呢～\n邀請長門櫻加入您的伺服器，一起開始冒險吧❤️",
                color=discord.Color.from_rgb(255, 182, 193)
            )
            embed.set_thumbnail(url=user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        
        # 計算總等級和總經驗值
        total_exp = sum(data['EXP'] for data in all_levels.values())
        max_level = max(data['Lv'] for data in all_levels.values())
        server_count = len(all_levels)
        
        embed = discord.Embed(
            title=f"🌸 {user.display_name} 的跨界冒險者資料",
            description=f"（驕傲地展示資料）主人在 {server_count} 個世界都留下了足跡呢❤️",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_thumbnail(url=user.avatar.url)
        
        # 總覽資訊
        embed.add_field(
            name="🌍 跨界統計",
            value=f"**活躍世界：** {server_count} 個\n**最高等級：** Lv.{max_level}\n**總經驗值：** {total_exp:,} EXP",
            inline=False
        )
        
        # 各伺服器詳細資訊
        for guild_id, data in all_levels.items():
            guild = self.bot.get_guild(int(guild_id))
            guild_name = guild.name if guild else f"未知伺服器 ({guild_id})"
            
            level = data['Lv']
            exp = data['EXP']
            level_title = self.get_level_title(level)
            
            embed.add_field(
                name=f"🏰 {guild_name}",
                value=f"**等級：** Lv.{level}\n**稱號：** {level_title}\n**經驗值：** {exp:,} EXP",
                inline=True
            )
        
        embed.add_field(
            name="用戶ID",
            value=f"`{user.id}`",
            inline=False
        )
        
        embed.set_footer(
            text="長門櫻見證您的跨界冒險旅程❤️ | 私聊模式 - 顯示所有伺服器資料"
        )
        
        await interaction.response.send_message(embed=embed)

    # ==================== Version版本功能 ====================
    
    def create_version_message(self, version):
        version_message = f"# 長門櫻 {version} \n"
        version_message += f"主人～這是長門櫻目前的版本資訊呢❤️\n\n"
        version_message += f"### 🎊 重要變更 \n\n"
        version_message += f" - **【重大】** 基礎功能整合 - 將DM、Help、Level、Version、Core功能整合到單一模組，大幅提升載入速度。\n"
        version_message += f" - **【重大】** 資產調整，將原本的 png 改為 jpg 大幅減少了儲存庫容量並且提升了部分程式在 discord 的回應速度。\n"
        version_message += f" - **【整合】** Game.py 整合了 GuessingGame.py 及 SnakeGame.py 以後遊戲相關的功能將全部整合在這裡。\n"
        version_message += f" - **【整合】** Image.py 整合了 Image.py 及 SuperDeformed.py 以後圖像相關的功能將全部整合在這裡。\n"
        version_message += f" - **【整合】** Math.py 整合了 Math.py 及 PrimeNumber.py 以後計算相關的功能將全部整合在這裡。\n\n"
        
        version_message += f"### ✨ 新增功能 \n\n"
        version_message += f" - **【新增】** BasicFeatures.py - 全新的基礎功能整合模組，包含所有核心功能。\n"
        version_message += f" - **【更新】** 所有基礎功能都支援斜線指令格式。\n"
        version_message += f" - **【增強】** 等級系統加入稱號、進度條和詳細統計。\n"
        version_message += f" - **【新增】** 系統資源監控功能。\n"
        version_message += f" - **【新增】** 每日簽到和狀態查詢功能。\n\n"
        
        version_message += f"### ⚠️ 已知問題 \n\n"
        version_message += f" - **【錯誤】** Youtube.py 使用/play [網址] 指令時，如果是播放清單會高機率報錯 (處理超時) ，建議使用播放清單時使用 !Play [網址] 來避免程式超時導致的報錯。\n\n"
        
        return version_message

    def get_system_info(self):
        """獲取系統資訊"""
        try:
            system = platform.system()
            release = platform.release()
            architecture = platform.architecture()[0]
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            memory = psutil.virtual_memory()
            memory_total = round(memory.total / (1024**3), 2)
            memory_used = round(memory.used / (1024**3), 2)
            memory_percent = memory.percent
            
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            return {
                "system": f"{system} {release}",
                "architecture": architecture,
                "python_version": python_version,
                "memory_total": memory_total,
                "memory_used": memory_used,
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count
            }
        except Exception as e:
            return None

    @commands.command(aliases=["VERSION","version","Ver"])
    async def Version(self, ctx):
        """Version版本指令"""
        version_message = self.create_version_message(self.version)
        
        # 只發送版本訊息，不再包含系統資訊
        await ctx.send(version_message, file=discord.File(self.output_path))

    @app_commands.command(name="version", description="顯示長門櫻當前版本")
    async def version(self, interaction: discord.Interaction):
        """Version版本斜線指令"""
        version_message = self.create_version_message(self.version)
        
        # 只發送版本訊息，不再包含系統資訊
        await interaction.response.send_message(version_message, file=discord.File(self.output_path))

    # ==================== Systeminfo系統資訊功能 ====================
    
    @commands.command(aliases=["SYSTEMINFO","systeminfo","sysinfo"])
    async def Systeminfo(self, ctx):
        """Systeminfo系統資訊指令"""
        system_embed = discord.Embed(
            title="📋 系統資訊",
            description="（認真地整理資料）這裡是長門櫻的詳細系統資訊喔～",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        # 機器人基本資訊
        system_embed.add_field(
            name="🤖 機器人資訊",
            value=f"**版本：** {self.version}\n**名稱：** {self.bot.user.name}\n**ID：** {self.bot.user.id}",
            inline=True
        )
        
        # Discord.py 版本
        system_embed.add_field(
            name="📚 框架版本",
            value=f"**discord.py：** {discord.__version__}\n**延遲：** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # 伺服器統計
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members()))
        system_embed.add_field(
            name="📊 服務統計",
            value=f"**伺服器數：** {guild_count}\n**用戶數：** {user_count}",
            inline=True
        )
        
        # 系統資訊
        system_info = self.get_system_info()
        if system_info:
            system_embed.add_field(
                name="💻 系統資訊",
                value=f"**系統：** {system_info['system']}\n**架構：** {system_info['architecture']}\n**Python：** {system_info['python_version']}",
                inline=True
            )
            
            system_embed.add_field(
                name="🧠 記憶體使用",
                value=f"**使用：** {system_info['memory_used']}GB / {system_info['memory_total']}GB\n**使用率：** {system_info['memory_percent']}%",
                inline=True
            )
            
            system_embed.add_field(
                name="⚡ CPU 使用",
                value=f"**使用率：** {system_info['cpu_percent']}%\n**核心數：** {system_info['cpu_count']}",
                inline=True
            )
        
        system_embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        system_embed.timestamp = datetime.datetime.now()
        
        await ctx.send(embed=system_embed)

    @app_commands.command(name="systeminfo", description="顯示長門櫻的詳細系統資訊")
    async def systeminfo(self, interaction: discord.Interaction):
        """Systeminfo系統資訊斜線指令"""
        system_embed = discord.Embed(
            title="📋 系統資訊",
            description="（認真地整理資料）這裡是長門櫻的詳細系統資訊喔～",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        # 機器人基本資訊
        system_embed.add_field(
            name="🤖 機器人資訊",
            value=f"**版本：** {self.version}\n**名稱：** {self.bot.user.name}\n**ID：** {self.bot.user.id}",
            inline=True
        )
        
        # Discord.py 版本
        system_embed.add_field(
            name="📚 框架版本",
            value=f"**discord.py：** {discord.__version__}\n**延遲：** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # 伺服器統計
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members()))
        system_embed.add_field(
            name="📊 服務統計",
            value=f"**伺服器數：** {guild_count}\n**用戶數：** {user_count}",
            inline=True
        )
        
        # 系統資訊
        system_info = self.get_system_info()
        if system_info:
            system_embed.add_field(
                name="💻 系統資訊",
                value=f"**系統：** {system_info['system']}\n**架構：** {system_info['architecture']}\n**Python：** {system_info['python_version']}",
                inline=True
            )
            
            system_embed.add_field(
                name="🧠 記憶體使用",
                value=f"**使用：** {system_info['memory_used']}GB / {system_info['memory_total']}GB\n**使用率：** {system_info['memory_percent']}%",
                inline=True
            )
            
            system_embed.add_field(
                name="⚡ CPU 使用",
                value=f"**使用率：** {system_info['cpu_percent']}%\n**核心數：** {system_info['cpu_count']}",
                inline=True
            )
        
        system_embed.set_footer(
            text="長門櫻 • 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        system_embed.timestamp = datetime.datetime.now()
        
        await interaction.response.send_message(embed=system_embed)

    # ==================== Core核心功能 ====================
    
    @commands.command()
    async def status(self, ctx):
        """查看機器人狀態"""
        uptime = datetime.datetime.now() - self.startup_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_embed = discord.Embed(
            title="🌸 長門櫻狀態報告",
            description="（認真地檢查狀態）主人～這是長門櫻目前的運行狀態❤️",
            color=discord.Color.green()
        )
        
        status_embed.add_field(
            name="⏰ 運行時間",
            value=f"{days}天 {hours}小時 {minutes}分鐘 {seconds}秒",
            inline=True
        )
        
        status_embed.add_field(
            name="📡 延遲",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        status_embed.add_field(
            name="🏠 伺服器數量",
            value=f"{len(self.bot.guilds)}個",
            inline=True
        )
        
        status_embed.add_field(
            name="👥 用戶數量",
            value=f"{len(set(self.bot.get_all_members()))}人",
            inline=True
        )
        
        status_embed.add_field(
            name="📝 載入的擴展",
            value=f"{len(self.bot.cogs)}個",
            inline=True
        )
        
        # 檢查狀態顏色
        if self.bot.latency < 0.1:
            status_color = "🟢 優秀"
        elif self.bot.latency < 0.2:
            status_color = "🟡 良好"
        else:
            status_color = "🔴 需要關注"
            
        status_embed.add_field(
            name="📊 整體狀態",
            value=status_color,
            inline=True
        )
        
        await ctx.send(embed=status_embed)
        
    @app_commands.command(name="status", description="查看長門櫻的運行狀態")
    async def status_slash(self, interaction: discord.Interaction):
        """查看機器人狀態 (斜線指令版本)"""
        uptime = datetime.datetime.now() - self.startup_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_embed = discord.Embed(
            title="🌸 長門櫻狀態報告",
            description="（認真地檢查狀態）主人～這是長門櫻目前的運行狀態❤️",
            color=discord.Color.green()
        )
        
        status_embed.add_field(
            name="⏰ 運行時間",
            value=f"{days}天 {hours}小時 {minutes}分鐘 {seconds}秒",
            inline=True
        )
        
        status_embed.add_field(
            name="📡 延遲",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        status_embed.add_field(
            name="🏠 伺服器數量",
            value=f"{len(self.bot.guilds)}個",
            inline=True
        )
        
        status_embed.add_field(
            name="👥 用戶數量",
            value=f"{len(set(self.bot.get_all_members()))}人",
            inline=True
        )
        
        status_embed.add_field(
            name="📝 載入的擴展",
            value=f"{len(self.bot.cogs)}個",
            inline=True
        )
        
        # 檢查狀態顏色
        if self.bot.latency < 0.1:
            status_color = "🟢 優秀"
        elif self.bot.latency < 0.2:
            status_color = "🟡 良好"
        else:
            status_color = "🔴 需要關注"
            
        status_embed.add_field(
            name="📊 整體狀態",
            value=status_color,
            inline=True
        )
        
        await interaction.response.send_message(embed=status_embed)
        
    @commands.command()
    async def about(self, ctx):
        """關於長門櫻"""
        about_embed = discord.Embed(
            title="🌸 關於長門櫻 🌸",
            description="（輕輕行禮，尾巴溫柔地搖擺）\n讓長門櫻來為主人介紹一下自己吧❤️",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        about_embed.add_field(
            name="👤 基本資料",
            value="**姓名：** 長門櫻 (Nagato Sakura)\n**代號：** NS-00\n**生日：** 2023年9月19日\n**種族：** 狐族獸人",
            inline=True
        )
        
        about_embed.add_field(
            name="🌟 外貌特徵",
            value="**髮色：** 金色長髮\n**瞳色：** 粉紫色\n**特徵：** 狐耳與尾巴\n**身高：** 165cm",
            inline=True
        )
        
        about_embed.add_field(
            name="💫 背景故事",
            value="來自異次元「常夜界」的狐耳獸娘\n受創造者天野靜樹大人的旨意\n守護神樹並引領異世界的來訪者",
            inline=False
        )
        
        about_embed.add_field(
            name="🎭 性格特質",
            value="• 樂觀活潑 • 親切溫柔 • 可愛俏皮\n• 對主人暗懷好感但不敢表達\n• 情感敏感且深情克制",
            inline=False
        )
        
        about_embed.add_field(
            name="🔧 開發資訊",
            value=f"**創造者：** 天野靜樹\n**框架：** discord.py {discord.__version__}\n**語言：** Python\n**啟動時間：** {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
        
        about_embed.set_footer(
            text="長門櫻永遠為主人服務❤️ | 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        
        await ctx.send(embed=about_embed)
        
    @app_commands.command(name="about", description="了解長門櫻的詳細資訊")
    async def about_slash(self, interaction: discord.Interaction):
        """關於長門櫻 (斜線指令版本)"""
        about_embed = discord.Embed(
            title="🌸 關於長門櫻 🌸",
            description="（輕輕行禮，尾巴溫柔地搖擺）\n讓長門櫻來為主人介紹一下自己吧❤️",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        about_embed.add_field(
            name="👤 基本資料",
            value="**姓名：** 長門櫻 (Nagato Sakura)\n**代號：** NS-00\n**生日：** 2023年9月19日\n**種族：** 狐族獸人",
            inline=True
        )
        
        about_embed.add_field(
            name="🌟 外貌特徵",
            value="**髮色：** 金色長髮\n**瞳色：** 粉紫色\n**特徵：** 狐耳與尾巴\n**身高：** 165cm",
            inline=True
        )
        
        about_embed.add_field(
            name="💫 背景故事",
            value="來自異次元「常夜界」的狐耳獸娘\n受創造者天野靜樹大人的旨意\n守護神樹並引領異世界的來訪者",
            inline=False
        )
        
        about_embed.add_field(
            name="🎭 性格特質",
            value="• 樂觀活潑 • 親切溫柔 • 可愛俏皮\n• 對主人暗懷好感但不敢表達\n• 情感敏感且深情克制",
            inline=False
        )
        
        about_embed.add_field(
            name="🔧 開發資訊",
            value=f"**創造者：** 天野靜樹\n**框架：** discord.py {discord.__version__}\n**語言：** Python\n**啟動時間：** {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
        
        about_embed.set_footer(
            text="長門櫻永遠為主人服務❤️ | 常夜界神樹守護者",
            icon_url=self.bot.user.avatar
        )
        
        await interaction.response.send_message(embed=about_embed)

    @commands.command()
    async def daily(self, ctx):
        """每日簽到功能"""
        daily_messages = [
            "（開心地蹦蹦跳跳）主人今天也來簽到了呢～長門櫻好開心❤️",
            "（尾巴興奮地搖擺）每天都能見到主人，是長門櫻最幸福的事情呢～",
            "（狐耳靈敏地豎起）主人今天的心情如何呢？長門櫻隨時為您服務～",
            "（溫柔地微笑）又是美好的一天開始了！主人今天要做什麼有趣的事呢？",
            "（害羞地低頭）主、主人今天也很帥氣呢...長門櫻的心跳好快❤️"
        ]
        
        daily_embed = discord.Embed(
            title="🌸 每日簽到 🌸",
            description=random.choice(daily_messages),
            color=discord.Color.from_rgb(255, 182, 193)
        )
        
        daily_embed.add_field(
            name="📅 今日日期",
            value=datetime.datetime.now().strftime("%Y年%m月%d日"),
            inline=True
        )
        
        daily_embed.add_field(
            name="🎁 每日祝福",
            value="願主人今天一切順利！❤️",
            inline=True
        )
        
        await ctx.send(embed=daily_embed)
        
    @app_commands.command(name="daily", description="每日簽到，獲得長門櫻的祝福")
    async def daily_slash(self, interaction: discord.Interaction):
        """每日簽到功能 (斜線指令版本)"""
        daily_messages = [
            "（開心地蹦蹦跳跳）主人今天也來簽到了呢～長門櫻好開心❤️",
            "（尾巴興奮地搖擺）每天都能見到主人，是長門櫻最幸福的事情呢～",
            "（狐耳靈敏地豎起）主人今天的心情如何呢？長門櫻隨時為您服務～",
            "（溫柔地微笑）又是美好的一天開始了！主人今天要做什麼有趣的事呢？",
            "（害羞地低頭）主、主人今天也很帥氣呢...長門櫻的心跳好快❤️"
        ]
        daily_embed = discord.Embed(
            title="🌸 每日簽到 🌸",
            description=random.choice(daily_messages),
            color=discord.Color.from_rgb(255, 182, 193)
        )
        daily_embed.add_field(
            name="📅 今日日期",
            value=datetime.datetime.now().strftime("%Y年%m月%d日"),
            inline=True
        )
        daily_embed.add_field(
            name="🎁 每日祝福",
            value="願主人今天一切順利！❤️",
            inline=True
        )
        await interaction.response.send_message(embed=daily_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(BasicFeatures(bot))
    print("Basic.py is ready")