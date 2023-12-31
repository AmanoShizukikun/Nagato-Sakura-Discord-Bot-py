import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json

# 設備選擇如果有NVIDIA顯卡切換為CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 環境檢測
print("<環境檢測>")
print(f"PyTorch版本 : {torch.__version__}")
print(f"訓練設備 : {device}")

# 詞彙表生成
print("<詞彙表生成>")
# 取得程式當前運行的資料夾路徑
current_directory = os.path.dirname(os.path.abspath(__file__))
# 載入訓練數據
json_model_path = os.path.join(current_directory, 'greeting_data.json')
with open(json_model_path, 'r', encoding='utf-8') as json_file:
    model_data = json.load(json_file)
# 提取訓練數據
instructions = [item["instruction"] for item in model_data]
outputs = [item["output"] for item in model_data]
# 用outputs 0或1 來分類是否為打招呼
greetings = [instruction for instruction, output in zip(instructions, outputs) if output == 1]
non_greetings = [instruction for instruction, output in zip(instructions, outputs) if output == 0]
# 提取詞彙表文字
vocab_text = []
for value in model_data:
    if 'weight' in value:
        vocab_text.extend(value)
# 將數據標記為打招呼和非打招呼
data = [(text, 1) for text in greetings] + [(text, 0) for text in non_greetings]
# 創建詞彙表 vocab
vocab = list(set(''.join([text for text, _ in data])))
# 將 vocab 保存為 tokenizer.json
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
train_data = [(text_to_vector(text), [label]) for text, label in data]

print("<訓練開始>")

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

# 設置模型參數
input_size = len(vocab)
hidden_size = 1024
output_size = 1

# 初始化模型、損失函數和優化器
model = GreetingClassifier(input_size, hidden_size, output_size)
criterion = nn.BCELoss()
optimizer = optim.SGD(model.parameters(), lr=1e-3)

# 訓練模型
epochs = 150
for epoch in range(epochs):
    total_loss = 0
    for text, label in train_data:
        optimizer.zero_grad()
        inputs = torch.tensor(text, dtype=torch.float)
        label = torch.tensor(label, dtype=torch.float)
        output = model(inputs)
        loss = criterion(output, label)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        
    # 輸出每個 epoch 的平均損失
    average_loss = total_loss / len(train_data)
    print(f"Epoch [{epoch + 1}/{epochs}], Loss: {average_loss:.4f}")
    
# 訓練結束 
print("訓練完成")


print("<生成模型配置文件>")
# 定義模型配置
model_config = {
    "_name_or_path": "your_model_name_or_path",
    "model_type": "your_model_type",
    "architectures": [
        "YourModelArchitecture"
    ],
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "learning_rate": optimizer.param_groups[0]['lr'],
}
model_config["_name_or_path"] = "Project Hello"
model_config["model_type"] = "Project Hello"
model_config["architectures"] = ["Project Hello Model"]

# 儲存模型配置為 config.json
config_path = os.path.join(current_directory, 'config.json')
with open(config_path, 'w') as json_file:
    json.dump(model_config, json_file, indent=4)
print(f"模型配置文件生成完成 模型配置文件儲存於 {config_path}")

print("<保存模型>")
model_path = os.path.join(current_directory, 'greeting_model.bin')
torch.save(model.state_dict(), model_path)
print(f"保存模型完成 模型保存於 {model_path}")


print("<載入測試模式>")
# 在載入模型權重之前定義 model_path
model_path = os.path.join(current_directory, 'greeting_model.bin')
# 載入模型並將其移到 CUDA 上
model = GreetingClassifier(input_size, hidden_size, output_size)
model = model.to(device)
# 加載模型權重
model.load_state_dict(torch.load(model_path))

# 測試模型
def predict_greeting(text):
    input_vector = torch.tensor(text_to_vector(text), dtype=torch.float)
    input_vector = input_vector.to(device)  
    output = model(input_vector)
    prediction = output.item()
    print(f"'{text}' 的預測值: {prediction}")
    return prediction

# 測試預設範例
test_sentences = ["你好啊！天氣真不錯，心情如何？", "我計畫著一趟旅行，探索一些我從未去過的地方。", "哈囉！好久不見，有什麼新鮮事嗎？", "我正在學習一種新的語言，雖然有點困難，但感覺很有成就感。"]
for sentence in test_sentences:
    print("<測試開始>")
    prediction = predict_greeting(sentence)
    if prediction > 0.9:
        print(f"'{sentence}' 是打招呼")
    else:
        print(f"'{sentence}' 不是打招呼")
print("測試完成")
