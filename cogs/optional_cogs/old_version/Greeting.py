import discord
from discord.ext import commands
import torch
import torch.nn as nn
import numpy as np
import json
from pathlib import Path
import os

class Greeting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MODEL_PATH = os.path.abspath('./data/Greeting/greeting_model.bin')
        self.VOCAB_PATH = os.path.abspath('./data/Greeting/tokenizer.json')
        self.CONFIG_PATH = os.path.abspath('./data/Greeting/config.json')
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.vocab = self.load_model(self.MODEL_PATH, self.VOCAB_PATH, self.CONFIG_PATH, self.device)

    def text_to_vector(self, text):
        vector = [0] * len(self.vocab)
        for word in text:
            if word in self.vocab:
                vector[self.vocab.index(word)] = 1
        return torch.tensor(vector, dtype=torch.float, device=self.device)

    def load_model(self, model_path, vocab_path, config_path, device):
        with open(vocab_path, 'r') as json_file:
            vocab = json.load(json_file)

        with open(config_path, 'r') as json_file:
            model_config = json.load(json_file)

        model = GreetingClassifier(model_config['input_size'], model_config['hidden_size'], model_config['output_size'])
        model.load_state_dict(torch.load(model_path))
        model = model.to(device)
        model.eval()

        return model, vocab
    
    def predict_greeting(self, text):
        input_vector = self.text_to_vector(text)
        output = self.model(input_vector)
        prediction = output.item()
        return prediction

    @commands.command(aliases=["greet","greeting","GREETING","Greet"])
    async def Greeting(self, ctx, *, text=None):
        if text is None:
            await ctx.send("主人~請輸入文字人家才能判斷是否為打招呼的意圖！")
            return
        
        prediction = self.predict_greeting(text)
        if prediction > 0.9:
            await ctx.send(f"長門櫻判斷 '{text}' 是打招呼，預測值為: {prediction}")
        else:
            await ctx.send(f"長門櫻判斷 '{text}' 不是打招呼，預測值為: {prediction}")

class GreetingClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(GreetingClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.sigmoid(x)
        return x

async def setup(bot):
    await bot.add_cog(Greeting(bot))
    print("Greeting.py is ready")
