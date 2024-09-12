import discord
from discord.ext import commands
import torch
import torch.nn as nn
import numpy as np
import json
from pathlib import Path
import os

class AutoReplyClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1, dropout=0.0):
        super(AutoReplyClassifier, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        batch_size = x.size(0)
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        out, _ = self.lstm(x.unsqueeze(1), (h0, c0))
        out = self.fc(out[:, -1, :])
        out = self.softmax(out)
        return out
    
class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MODEL_PATH = os.path.abspath('./data/AutoReply/AutoReply_model.bin')
        self.VOCAB_PATH = os.path.abspath('./data/AutoReply/tokenizer.json')
        self.CONFIG_PATH = os.path.abspath('./data/AutoReply/config.json')
        self.LABEL_PATH = os.path.abspath('./data/AutoReply/labels.txt')
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.vocab, self.label_mapping = self.load_model(self.MODEL_PATH, self.VOCAB_PATH, self.CONFIG_PATH, self.LABEL_PATH)

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
    
    def text_to_vector(self, text):
        vector = [0] * len(self.vocab)
        for word in text:
            if word in self.vocab:
                vector[self.vocab.index(word)] = 1
        return vector
    
    def predict_AutoReply(self, text):
        input_vector = self.text_to_vector(text)
        input_vector = torch.tensor(input_vector, dtype=torch.float).unsqueeze(0).to(self.device)
        output = self.model(input_vector)
        predicted_class = torch.argmax(output).item()
        predicted_probs = output.squeeze().tolist()
        predicted_label = [label for label, index in self.label_mapping.items() if index == predicted_class][0]
        max_prob_value = max(predicted_probs)
        result = f"Predicted Label: {predicted_label}, Highest Probability: {max_prob_value}"
        return result

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        mentioned = self.bot.user.mentioned_in(message) 
        has_content = bool(message.content.strip()) 
        if mentioned and has_content and len(message.content) > len(self.bot.user.mention):
            text = message.content
            result = self.predict_AutoReply(text)
            await message.channel.send(result)
    
async def setup(bot):
    await bot.add_cog(AutoReply(bot))
    print("AutoReply.py is ready")