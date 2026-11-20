import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import json
from tqdm import tqdm
import time

# 設備選擇如果有NVIDIA顯卡切換為CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("<環境檢測>")
print(f"PyTorch版本 : {torch.__version__}")
print(f"訓練設備 : {device}")

# 取得程式當前運行的資料夾路徑
current_directory = os.path.dirname(os.path.abspath(__file__))

# 定義模型
class AutoReplyClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1, dropout=0.1):
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
    
# 生成詞彙表
print("<詞彙表生成>")
json_model_path = os.path.join(current_directory, 'AutoReply_data.json')
with open(json_model_path, 'r', encoding='utf-8') as json_file:
    model_data = json.load(json_file)
instructions = [item["instruction"] for item in model_data]
outputs = [item["output"] for item in model_data]
vocab_text = []
for value in model_data:
    if 'weight' in value:
        vocab_text.extend(value)
        
# 生成標籤編號將標籤儲存為 labels.txt
print("<類別標籤生成>")
label_mapping = {}
label_count = 0
for label in outputs:
    if label not in label_mapping:
        label_mapping[label] = label_count
        label_count += 1
labels_path = os.path.join(current_directory, 'labels.txt')
with open(labels_path, 'w', encoding='utf-8') as labels_file:
    for label, index in label_mapping.items():
        labels_file.write(f"{label}: {index}\n")
print(f"標籤已儲存於 {labels_path}")
print(f"類別標籤生成完成 Lables 儲存為 .txt 於 {labels_path}")

# 創建詞彙表 vocab
vocab = list(set(''.join([text for text in instructions])))
tokenizer_path = os.path.join(current_directory, 'tokenizer.json')
with open(tokenizer_path, 'w') as json_file:
    json.dump(vocab, json_file, indent=2)
print(f"詞彙表生成完成 Tokenizer 儲存為 .json 於 {tokenizer_path}")

# 將文本轉換為向量
def text_to_vector(text):
    vector = [0] * len(vocab)
    for word in text:
        if word in vocab:
            vector[vocab.index(word)] = 1
    return vector

# 將數據轉換為模型可用的格式
train_data = [(text_to_vector(text), label_mapping[label]) for text, label in zip(instructions, outputs)]

print("<訓練開始>")
# 設置模型參數
input_size = len(vocab)
hidden_size = 2048
output_size = len(label_mapping)

# 初始化模型、損失函數和優化器
model = AutoReplyClassifier(input_size, hidden_size, output_size)
model = model.to(device) 
criterion = nn.CrossEntropyLoss() 
criterion = criterion.to(device)  
optimizer = optim.SGD(model.parameters(), lr=2)

# 記錄開始訓練時間
training_start_time = time.time()

# 將數據轉換為 DataLoader 所需的張量
features = [text_to_vector(text) for text in instructions]
labels = [label_mapping[label] for label in outputs]
tensor_x = torch.tensor(features, dtype=torch.float)
tensor_y = torch.tensor(labels, dtype=torch.long)
dataset = TensorDataset(tensor_x, tensor_y)

# 創建 DataLoader 來加載批次數據
batch_size = 64
train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# 訓練模型
epochs = 100000
for epoch in range(epochs):
    total_loss = 0
    start_time = time.time()

    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        output = model(batch_x)
        loss = criterion(output, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        
    average_loss = total_loss / len(train_loader)
    elapsed_time = time.time() - start_time
    eta = (epochs - epoch - 1) * elapsed_time
    total_training_time = time.time() - training_start_time
    progress = epoch + 1
    percentage = progress / epochs * 100
    fill_length = int(50 * progress / epochs)
    space_length = 50 - fill_length
    print(f"Processing: {percentage:3.0f}%|{'█' * fill_length}{' ' * space_length}| {progress}/{epochs} [{total_training_time:.2f}<{eta:.2f}, {1 / elapsed_time:.2f}it/s, Loss: {average_loss:.4f}] ")
    
print("訓練完成")

print("<生成模型配置文件>")
model_config = {
    "_name_or_path": "AmanoShizukikun/Nagato-Sakura-AutoReply",
    "model_type": "Nagato-Sakura-AutoReply",
    "architectures": ["Nagato-Sakura-AutoReply"],
    "version": "AutoReply_V3",
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "learning_rate": optimizer.param_groups[0]['lr'],
}
config_path = os.path.join(current_directory, 'config.json')
with open(config_path, 'w') as json_file:
    json.dump(model_config, json_file, indent=4)
print(f"模型配置文件生成完成 模型配置文件儲存於 {config_path}")

print("<保存模型>")
model_path = os.path.join(current_directory, 'AutoReply_model.bin')
torch.save(model.state_dict(), model_path)
print(f"保存模型完成 模型保存於 {model_path}")

print("<載入測試模式>")
model_path = os.path.join(current_directory, 'AutoReply_model.bin')
model = AutoReplyClassifier(input_size, hidden_size, output_size)
model = model.to(device)
model.load_state_dict(torch.load(model_path))

# 測試模型
def predict_AutoReply(text):
    input_vector = text_to_vector(text)  # 取得文字向量
    input_vector = torch.tensor(input_vector, dtype=torch.float).unsqueeze(0).to(device)  # 調整張量形狀並移到裝置上
    output = model(input_vector)
    predicted_class = torch.argmax(output).item()
    predicted_probs = output.squeeze().tolist()  # 預測機率列表
    predicted_label = [label for label, index in label_mapping.items() if index == predicted_class][0]
    print(f"'{text}'  預測概率: {predicted_probs}")
    print(f"預測結果: {predicted_label}")
    return predicted_label, predicted_probs, predicted_class

# 測試預設範例
test_sentences = [
    "你好，你會說中文嗎", 
    "你是誰？", 
    "你能夠提供哪些類型的幫助？", 
    "你是OpenAI開發的什麼？"
    ]

for sentence in test_sentences:
    print("<測試開始>")
    predicted_label, predicted_probs, predicted_class = predict_AutoReply(sentence)
print("<測試完成>")
