import discord
from discord.ext import commands
import torch
import torch.nn as nn
import numpy as np
import json
from pathlib import Path
import os

class CheckSMS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MODEL_PATH = os.path.abspath('./models/CheckSMS/SMS_model.bin')
        self.VOCAB_PATH = os.path.abspath('./models/CheckSMS/tokenizer.json')
        self.CONFIG_PATH = os.path.abspath('./models/CheckSMS/config.json')
        self.LABEL_PATH = os.path.abspath('./models/CheckSMS/labels.txt')
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.vocab, self.label_mapping = self.load_model(self.MODEL_PATH, self.VOCAB_PATH, self.CONFIG_PATH, self.LABEL_PATH)

    def text_to_vector(self, text):
        vector = [0] * len(self.vocab)
        for word in text:
            if word in self.vocab:
                vector[self.vocab.index(word)] = 1
        return torch.tensor(vector, dtype=torch.float, device=self.device)

    def load_model(self, model_path, vocab_path, config_path, label_path):
        with open(vocab_path, 'r') as json_file:
            vocab = json.load(json_file)

        with open(config_path, 'r') as json_file:
            model_config = json.load(json_file)
        
        with open(label_path, 'r') as labels_file:
            label_mapping = {}
            for line in labels_file:
                label, index = line.strip().split(': ')
                label_mapping[label] = int(index)

        model = CheckSMSClassifier(model_config['input_size'], model_config['hidden_size'], model_config['output_size'])
        model.load_state_dict(torch.load(model_path))
        model = model.to(self.device)
        model.eval()

        return model, vocab, label_mapping
    
    def predict_SMS(self, text):
        input_vector = self.text_to_vector(text)
        output = self.model(input_vector)
        probabilities = nn.functional.softmax(output, dim=-1)
        predicted_prob, predicted_class = torch.max(probabilities, dim=-1)
        return predicted_class.item(), predicted_prob.item()

    @commands.command(aliases=["checksms","CHECKSMS","SMS"])
    async def CheckSMS(self, ctx, *, text=None):
        if text is None:
            await ctx.send("主人~請輸入文字人家才能判斷簡訊的類別！")
            return
        predicted_class, predicted_prob = self.predict_SMS(text)
        predicted_label = list(self.label_mapping.keys())[list(self.label_mapping.values()).index(predicted_class)]
        await ctx.send(f"長門櫻判斷 '{text}' 是 {predicted_label}，預測概率為: {predicted_prob}")

class CheckSMSClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(CheckSMSClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.softmax(x)
        return x
    
async def setup(bot):
    await bot.add_cog(CheckSMS(bot))
    print("CheckSMS.py is ready")