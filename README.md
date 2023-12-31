# Discord-Bot-Nagato-Sakura-py

長門櫻 Discord.py 版本

## 近期變動
### 1.5.ι (2023 年 12 月 22 日)
![t2i](assets/1.5.ι.png)
### 重要
- 首個對外公開的版本
- 調整伺服器資料的儲存方式 (存放方式改為將資料存到server/伺服器ID/資料伺服器ID.json)
- 重製等級系統，所有等級歸0，大幅降低每等所需經驗值 (原本6等級^4/2.5改為6等級^2/2.5)

### 新增
- !VoteCreate [問題] [選項1] [選項2] [選項N] - 創建投票
- !Vote [問題] [選項名稱] - 投票
- !VoteResult [問題] - 顯示投票結果
- !join - 機器人進入語音聊天室
- !leave - 機器人離開語音聊天室 
- !play [網址] - 播放音樂(目前支援以下平台:StreetVoice)
- !GuessingGameStart - 開啟猜數字遊戲
- !Guess [數字] - 猜數字
- !Tarot - 抽塔羅牌
- !PrimeNumber [整數] - 判斷是否為質數
- !Greeting [文字] - 自製小型AI模型判斷文字是否為打招呼 (模型版本 : Project Hello Model 500)

### 故障
- !play [網址] - Youtube 複數影片清單無法播放
- !play [網址] - Youtube 無法累加播放清單

## 快速開始
 **粗體** 的是強制要求的。
 
### 硬體要求
1. 作業系統：Windows
1. **CPU** / Nvidia GPU

### 環境設置
- **Python 3**
- 下載: https://www.python.org/downloads/windows/
- **PyTorch**
- 下載: https://pytorch.org/
- NVIDIA GPU驅動程式
- 下載: https://www.nvidia.com/zh-tw/geforce/drivers/
- NVIDIA CUDA Toolkit
- 下載: https://developer.nvidia.com/cuda-toolkit
- NVIDIA cuDNN
- 下載: https://developer.nvidia.com/cudnn
- **FFMPEG**
- 下載: https://ffmpeg.org/download.html
```shell
python3 -m pip install -U discord.py
python3 -m pip install -U discord.py[voice]
pip install numpy
pip install numexpr
pip install googletrans==3.1.0a0
pip install requests
pip install openai
pip install youtube_dl
pip install Pillow
pip install beautifulsoup4
pip install --upgrade httpcore
```
### 環境變數
```shell
C:\Program Files\ffmpeg-master-latest-win64-gpl\bin
```
### youtube_dl修復
1. 尋找youtube-dl中的youtube.py
```shell
"C:\Users\使用者名稱\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
```
2. 修改youtube.py 修改第1794行 :
```shell
'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
直接註釋
```shell
#'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
3. 儲存youtube.py

### Translate.py 修復(11月Google更新後的新錯誤)
1. 尋找googletrans中的client.py
```shell
"C:\Users\使用者名稱\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\googletrans\client.py"
```
2. 修改client.py 修改第57行 :
```shell
proxies: typing.Dict[str, httpcore.SyncHTTPTransport] = None,
```
改為
```shell
proxies: typing.Dict[str, httpcore.AsyncHTTPProxy] = None,
```
3. 儲存client.py
