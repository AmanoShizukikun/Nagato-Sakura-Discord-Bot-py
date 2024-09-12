import discord
from discord.ext import commands
import torch
import torch.nn as nn
import numpy as np
import json
from pathlib import Path
import os

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MODEL_PATH = os.path.abspath('./data/AutoReply/AutoReply_model.bin')
        self.VOCAB_PATH = os.path.abspath('./data/AutoReply/tokenizer.json')
        self.CONFIG_PATH = os.path.abspath('./data/AutoReply/config.json')
        self.LABEL_PATH = os.path.abspath('./data/AutoReply/labels.txt')
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.vocab, self.label_mapping = self.load_model(self.MODEL_PATH, self.VOCAB_PATH, self.CONFIG_PATH, self.LABEL_PATH)

    def text_to_vector(self, text):
        vector = [0] * len(self.vocab)
        for word in text:
            if word in self.vocab:
                vector[self.vocab.index(word)] = 1
        return torch.tensor(vector, dtype=torch.float, device=self.device).unsqueeze(0)

    def load_model(self, model_path, vocab_path, config_path, label_path):
        with open(vocab_path, 'r', encoding='utf-8') as json_file:
            vocab = json.load(json_file)

        with open(config_path, 'r', encoding='utf-8') as json_file:
            model_config = json.load(json_file)
        
        with open(label_path, 'r', encoding='utf-8') as labels_file:
            label_mapping = {}
            for line in labels_file:
                label, index = line.strip().split(': ')
                label_mapping[label] = int(index)

        model = AutoReplyClassifier(model_config['input_size'], model_config['hidden_size'], model_config['output_size'])
        model.load_state_dict(torch.load(model_path))
        model = model.to(self.device)
        model.eval()

        return model, vocab, label_mapping
    
    def predict_AutoReply(self, text):
        input_vector = self.text_to_vector(text)
        output = self.model(input_vector)
        probabilities = nn.functional.softmax(output, dim=-1)
        predicted_prob, predicted_class = torch.max(probabilities, dim=-1)
        return predicted_class.item(), predicted_prob.item()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        mentioned = self.bot.user.mentioned_in(message) 
        has_content = bool(message.content.strip()) 
        if mentioned and has_content and len(message.content) > len(self.bot.user.mention):
            text = message.content
            predicted_class, predicted_prob = self.predict_AutoReply(text)
            predicted_label = list(self.label_mapping.keys())[list(self.label_mapping.values()).index(predicted_class)]
            
            threshold = 0.01
            if predicted_prob > threshold:
                await message.channel.send(f"{predicted_label}")
            else:
                await message.channel.send(f"抱歉啊主人~長門櫻無法理解主人在講甚麼。錯誤代碼: ({predicted_prob})")
                
class AutoReplyClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(AutoReplyClassifier, self).__init__()
        self.hidden_size = hidden_size
        self.rnn = nn.RNN(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        batch_size = x.size(0) 
        h0 = torch.zeros(1, batch_size, self.hidden_size).to(x.device) 
        out, _ = self.rnn(x.unsqueeze(1), h0)
        out = self.softmax(out)
        return out
    
async def setup(bot):
    await bot.add_cog(AutoReply(bot))
    print("AutoReply.py is ready")