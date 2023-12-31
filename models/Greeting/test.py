import torch
import torch.nn as nn
import numpy as np
import json
from pathlib import Path

# 取得目前執行程式的資料夾路徑
current_directory = Path(__file__).resolve().parent

# 定義神經網路模型
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

def text_to_vector(text, vocab, device):
    vector = [0] * len(vocab)
    for word in text:
        if word in vocab:
            vector[vocab.index(word)] = 1
    return torch.tensor(vector, dtype=torch.float, device=device)

def predict_greeting(text, model, vocab):
    device = next(model.parameters()).device
    input_vector = text_to_vector(text, vocab, device)
    output = model(input_vector)
    prediction = output.item()
    return prediction

# 加載模型和 vocab
def load_model(model_path, vocab_path, config_path, device):
    # 讀取 vocab
    with open(vocab_path, 'r') as json_file:
        vocab = json.load(json_file)
        
    # 讀取模型配置
    with open(config_path, 'r') as json_file:
        model_config = json.load(json_file)

    # 初始化模型並將其移到 CUDA 上
    model = GreetingClassifier(model_config['input_size'], model_config['hidden_size'], model_config['output_size'])
    model.load_state_dict(torch.load(model_path))
    model = model.to(device)
    model.eval()

    return model, vocab

# 模型資料路徑設定
MODEL_PATH = current_directory / "greeting_model.bin"
VOCAB_PATH = current_directory / "tokenizer.json"
CONFIG_PATH = current_directory / "config.json"

# 設備選擇如果有NVIDIA顯卡切換為CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 環境檢測
print("<環境檢測>")
print(torch.__version__)
print(device)

# 加载模型和 vocab
model, vocab = load_model(MODEL_PATH, VOCAB_PATH, CONFIG_PATH, device)

# 用戶輸入
print("<測試開始>")
user_input = input("請輸入一段文字：")
prediction = predict_greeting(user_input, model, vocab)

# 輸出結果
if prediction > 0.9:
    print(f"模型判斷 '{user_input}' 是打招呼，預測值為: {prediction}")
else:
    print(f"模型判斷 '{user_input}' 不是打招呼，預測值為: {prediction}")
