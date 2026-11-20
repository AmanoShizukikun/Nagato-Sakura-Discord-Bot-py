import discord
from discord import app_commands
from discord.ext import commands, tasks 
import json
import os
import math
import random
import asyncio
import datetime

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.save())
        self.server_id = str(self.bot.guilds[0].id)
        self.server_folder = f'./server/{self.server_id}'
        os.makedirs(self.server_folder, exist_ok=True)
        self.Level_file = f'{self.server_folder}/Level_{self.server_id}.json'
        
        try:
            with open(self.Level_file, "r") as file:
                self.users = json.load(file)
        except FileNotFoundError:
            self.users = {}
      
    def Level_up(self, author_id):
        current_EXP = self.users[author_id]["EXP"]
        current_Level = self.users[author_id]["Lv"]
    
        if current_EXP >= math.ceil((50 * (current_Level **1.3))):
            self.users[author_id]["Lv"] +=1
            return True
        else:
            return False
    
    def get_level_title(self, level):
        """根據等級返回稱號"""
        if level >= 100:
            return "🌟 常夜界傳說"
        elif level >= 80:
            return "👑 神樹守護者"
        elif level >= 60:
            return "⚔️ 禍墮討伐者"
        elif level >= 40:
            return "🌸 櫻花騎士"
        elif level >= 20:
            return "🦊 狐靈使者"
        elif level >= 10:
            return "✨ 見習冒險者"
        else:
            return "🌱 新手旅人"
    
    def get_next_level_exp(self, level):
        """計算下一等級所需經驗值"""
        return math.ceil((50 * (level **1.3)))
    
    def get_level_progress(self, current_exp, level):
        """計算等級進度條"""
        next_level_exp = self.get_next_level_exp(level)
        prev_level_exp = math.ceil((50 * ((level-1) **1.3))) if level > 1 else 0
        current_level_exp = current_exp - prev_level_exp
        exp_needed = next_level_exp - prev_level_exp
        
        progress = current_level_exp / exp_needed
        progress_bar_length = 20
        filled_length = int(progress_bar_length * progress)
        bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
        
        return f"[{bar}] {current_level_exp}/{exp_needed}"
    
    async def save(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            with open(self.Level_file, "w") as file:
                json.dump(self.users, file, indent=4)
            await asyncio.sleep(5)
  
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        author_id = str(message.author.id)
        if not author_id in self.users:
            self.users[author_id] = {}
            self.users[author_id]["Lv"] = 1
            self.users[author_id]["EXP"] = 0
            self.users[author_id]["messages_sent"] = 0
            self.users[author_id]["first_message_date"] = datetime.datetime.now().isoformat()
            
        random_EXP = random.randint(5,10)
        self.users[author_id]["EXP"] += random_EXP
        self.users[author_id]["messages_sent"] = self.users[author_id].get("messages_sent", 0) + 1
    
        if self.Level_up(author_id):
            current_level = self.users[author_id]['Lv']
            level_title = self.get_level_title(current_level)
            
            # 升級獎勵訊息
            level_up_messages = [
                f"（狐耳興奮地豎起）哇～主人升級了！現在是 {level_title} 了呢❤️",
                f"（開心地轉圈）恭喜主人！長門櫻感受到了主人更強的力量～",
                f"（尾巴搖得更歡快）主人越來越厲害了！{level_title} 真的很棒呢～",
                f"（雙眼閃閃發光）主人的成長讓長門櫻好開心❤️ {level_title} 的稱號很適合主人呢！"
            ]
            
            Lv_up_embed = discord.Embed(
                title="🌸 等級提升！🌸", 
                description=random.choice(level_up_messages),
                color=discord.Color.gold()
            )
            Lv_up_embed.set_thumbnail(url=message.author.avatar.url)
            Lv_up_embed.add_field(
                name="✨ 新等級", 
                value=f"**Lv.{current_level}**", 
                inline=True
            )
            Lv_up_embed.add_field(
                name="🏆 獲得稱號", 
                value=level_title, 
                inline=True
            )
            Lv_up_embed.add_field(
                name="📈 經驗值", 
                value=f"{self.users[author_id]['EXP']} EXP", 
                inline=True
            )
            
            await message.channel.send(embed=Lv_up_embed)
    
    @commands.command(aliases=["LV","level"])
    async def Level(self,ctx,user: discord.User=None):
        if user is None:
            user = ctx.author
        elif user is not None:
            user = user
            
        author_id = str(user.id)
        if author_id not in self.users:
            # 如果用戶不存在，創建基本資料
            self.users[author_id] = {
                "Lv": 1,
                "EXP": 0,
                "messages_sent": 0,
                "first_message_date": datetime.datetime.now().isoformat()
            }
            
        user_data = self.users[author_id]
        level = user_data['Lv']
        exp = user_data['EXP']
        level_title = self.get_level_title(level)
        progress_bar = self.get_level_progress(exp, level)
        
        roles = ', '.join([role.name for role in user.roles[1:]])  
        
        Lv_card = discord.Embed(
            title=f"🌸 {user.display_name} 的冒險者資料卡",
            description=f"**{level_title}**\n（長門櫻溫柔地微笑著為主人整理資料❤️）",
            color=discord.Color.from_rgb(255, 182, 193)
        ) 
        Lv_card.set_thumbnail(url=user.avatar.url)
        
        # 基本資訊
        Lv_card.add_field(
            name="👑 伺服器身份", 
            value=roles if roles else "一般成員", 
            inline=False
        )
        
        # 等級資訊
        Lv_card.add_field(
            name="⭐ 冒險者等級", 
            value=f"**Lv.{level}**", 
            inline=True
        )
        Lv_card.add_field(
            name="✨ 經驗值", 
            value=f"**{exp:,} EXP**", 
            inline=True
        )
        Lv_card.add_field(
            name="📊 等級進度", 
            value=progress_bar, 
            inline=False
        )
        
        # 統計資訊
        messages_count = user_data.get('messages_sent', 0)
        Lv_card.add_field(
            name="💬 訊息統計", 
            value=f"{messages_count:,} 則訊息", 
            inline=True
        )
        
        # 時間資訊
        join_date = user.joined_at.strftime("%Y年%m月%d日")
        first_msg_date = user_data.get('first_message_date')
        if first_msg_date:
            first_msg = datetime.datetime.fromisoformat(first_msg_date).strftime("%Y年%m月%d日")
        else:
            first_msg = "未知"
            
        Lv_card.add_field(
            name="📅 加入日期", 
            value=join_date, 
            inline=True
        )
        Lv_card.add_field(
            name="🌟 首次互動", 
            value=first_msg, 
            inline=True
        )
        
        Lv_card.add_field(
            name="🆔 用戶ID", 
            value=f"`{user.id}`", 
            inline=False
        )
        
        # 計算到下一等級的經驗值
        next_level_exp = self.get_next_level_exp(level)
        exp_needed = next_level_exp - exp
        
        Lv_card.set_footer(
            text=f"距離下一等級還需要 {exp_needed:,} 經驗值 | 長門櫻陪伴您的冒險旅程❤️"
        )
        
        await ctx.send(embed=Lv_card)
    
    @Level.error
    async def Remove_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("噫~糟糕！出現了一個錯誤：「多於輸入」不開放查看別人的個人資料卡")      
            
    @app_commands.command(name="level", description="!Level [用戶] - 顯示[用戶]資料卡")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user
            
        author_id = str(user.id)
        if author_id not in self.users:
            # 如果用戶不存在，創建基本資料
            self.users[author_id] = {
                "Lv": 1,
                "EXP": 0,
                "messages_sent": 0,
                "first_message_date": datetime.datetime.now().isoformat()
            }
            
        user_data = self.users[author_id]
        level = user_data['Lv']
        exp = user_data['EXP']
        level_title = self.get_level_title(level)
        progress_bar = self.get_level_progress(exp, level)
        
        roles = ', '.join([role.name for role in user.roles[1:]])  
        
        Lv_card = discord.Embed(
            title=f"🌸 {user.display_name} 的冒險者資料卡",
            description=f"**{level_title}**\n（長門櫻溫柔地微笑著為主人整理資料❤️）",
            color=discord.Color.from_rgb(255, 182, 193)
        ) 
        Lv_card.set_thumbnail(url=user.avatar.url)
        
        # 基本資訊
        Lv_card.add_field(
            name="👑 伺服器身份", 
            value=roles if roles else "一般成員", 
            inline=False
        )
        
        # 等級資訊
        Lv_card.add_field(
            name="⭐ 冒險者等級", 
            value=f"**Lv.{level}**", 
            inline=True
        )
        Lv_card.add_field(
            name="✨ 經驗值", 
            value=f"**{exp:,} EXP**", 
            inline=True
        )
        Lv_card.add_field(
            name="📊 等級進度", 
            value=progress_bar, 
            inline=False
        )
        
        # 統計資訊
        messages_count = user_data.get('messages_sent', 0)
        Lv_card.add_field(
            name="💬 訊息統計", 
            value=f"{messages_count:,} 則訊息", 
            inline=True
        )
        
        # 時間資訊
        join_date = user.joined_at.strftime("%Y年%m月%d日")
        first_msg_date = user_data.get('first_message_date')
        if first_msg_date:
            first_msg = datetime.datetime.fromisoformat(first_msg_date).strftime("%Y年%m月%d日")
        else:
            first_msg = "未知"
            
        Lv_card.add_field(
            name="📅 加入日期", 
            value=join_date, 
            inline=True
        )
        Lv_card.add_field(
            name="🌟 首次互動", 
            value=first_msg, 
            inline=True
        )
        
        Lv_card.add_field(
            name="🆔 用戶ID", 
            value=f"`{user.id}`", 
            inline=False
        )
        
        # 計算到下一等級的經驗值
        next_level_exp = self.get_next_level_exp(level)
        exp_needed = next_level_exp - exp
        
        Lv_card.set_footer(
            text=f"距離下一等級還需要 {exp_needed:,} 經驗值 | 長門櫻陪伴您的冒險旅程❤️"
        )
        
        await interaction.response.send_message(embed=Lv_card)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Level(bot))
    print("Level.py is ready")