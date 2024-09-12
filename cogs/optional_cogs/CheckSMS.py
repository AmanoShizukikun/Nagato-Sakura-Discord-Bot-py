import discord
from discord.ext import commands
import torch
import torch.nn as nn
import json
from pathlib import Path
import os
import re
import requests
import ssl
import socket

class SMSClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(SMSClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, int(hidden_size * 0.66))
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(int(hidden_size * 0.66), int(hidden_size * 0.66))
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(int(hidden_size * 0.66), output_size)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        x = self.relu2(x)
        x = self.fc3(x)
        x = self.softmax(x)
        return x

class CheckSMS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.MODEL_PATH = os.path.abspath('./data/CheckSMS/SMS_model.bin')
        self.VOCAB_PATH = os.path.abspath('./data/CheckSMS/tokenizer.json')
        self.CONFIG_PATH = os.path.abspath('./data/CheckSMS/config.json')
        self.LABEL_PATH = os.path.abspath('./data/CheckSMS/labels.txt')
        self.BLACKLIST_PATH = os.path.abspath('./data/CheckSMS/blacklist.txt')
        self.model, self.vocab, self.label_mapping = self.load_model(self.MODEL_PATH, self.VOCAB_PATH, self.CONFIG_PATH, self.LABEL_PATH, self.device)

    def load_model(self, model_path, vocab_path, config_path, label_path, device):
        with open(vocab_path, 'r') as json_file:
            vocab = json.load(json_file)
        with open(config_path, 'r') as json_file:
            model_config = json.load(json_file)
        with open(label_path, 'r') as labels_file:
            label_mapping = {}
            for line in labels_file:
                label, index = line.strip().split(': ')
                label_mapping[label] = int(index)
        model = SMSClassifier(model_config['input_size'], model_config['hidden_size'], model_config['output_size'])
        model.load_state_dict(torch.load(model_path))
        model = model.to(device)
        model.eval()
        return model, vocab, label_mapping

    def text_to_vector(self, text):
        vector = [0] * len(self.vocab)
        for word in text:
            if word in self.vocab:
                vector[self.vocab.index(word)] = 1
        return vector
    
    def predict_SMS(self, text):
        input_vector = self.text_to_vector(text)
        input_vector = torch.tensor(input_vector, dtype=torch.float).unsqueeze(0).to(self.device)
        output = self.model(input_vector)
        predicted_class = torch.argmax(output).item()
        predicted_probs = output.squeeze().tolist()
        predicted_label = [label for label, index in self.label_mapping.items() if index == predicted_class][0]
        phone_numbers = re.findall(r'(\(?0\d{1,2}\)?[-\.\s]?\d{3,4}[-\.\s]?\d{3,4})', text)
        urls = re.findall(r'\b(?:https?://)?(?:www\.)?[\w\.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?(?![\w\.-])\b', text)
        verification_codes = re.findall(r'(?<!\d)(\d{4,6})(?!\d)(?<!/)', text)
        result = f"主人~長門櫻已將簡訊解析完成，以下是解析的結果:\n"
        result += f"【簡訊內容】: {text}\n"
        result += f"【預測結果】: {predicted_label}\n"
        result += f"【預測概率】: {predicted_probs}\n"
        if phone_numbers:
            result += f"【偵測電話】: {phone_numbers}\n"
        if urls:
            for url in urls:
                with open(self.BLACKLIST_PATH, "r", encoding="utf-8") as file:
                    blacklist = set(line.strip() for line in file)
                for blacklisted_url in blacklist:
                    if blacklisted_url in urls:
                        result += f"【黑名單】 {urls} 在黑名單中\n"
                        break 
                result += f"{self.check_url_safety(url)}\n"
        if predicted_label == 'Captcha SMS':
            if verification_codes:
                result += f"【驗證碼】: {verification_codes}\n"
            else:
                result += f"【驗證碼】:未找到驗證碼。\n"
        return result
        
    def check_url_safety(self, url):
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            if not url.startswith("https://"):
                return f"【警告】 {url} 使用不安全的協議"
            suspicious_patterns = ["phishing", "malware", "hack", "top"]
            if any(pattern in url.lower() for pattern in suspicious_patterns):
                return f"【警告】 {url} 的路徑包含可疑模式"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"【安全】 {url} 是安全的"
            else:
                return f"【警告】 {url} 可能有風險 (狀態碼: {response.status_code})."
        except requests.exceptions.RequestException as e:
            return f"【錯誤】 {url}: 請求錯誤 ({str(e)})"
        except ssl.SSLError as ssl_error:
            return f"【警告】 {url} SSL 握手失敗 ({ssl_error.strerror})"
        except socket.timeout:
            return f"【錯誤】 {url}: 連接超時"
        except socket.error as socket_error:
            return f"【錯誤】 {url}: 連接錯誤 ({str(socket_error)})"
        except Exception as e:
            return f"【錯誤】 {url}: {str(e)}"

    @commands.command(aliases=["checksms","CHECKSMS","SMS"])
    async def CheckSMS(self, ctx, *, text=None):
        if text is None:
            await ctx.send("主人~請輸入文字人家才能判斷簡訊的類別！")
            return
        result = self.predict_SMS(text)
        await ctx.send(result)

async def setup(bot):
    await bot.add_cog(CheckSMS(bot))
    print("CheckSMS.py is ready")
