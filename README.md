# Nagato-Sakura-Discord-Bot-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py?style=social)](https://github.com/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py)](https://github.com/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py/commits/main)

\[ 中文 | [English](README_en.md) | [日本語](README_jp.md) \]

長門櫻 Discord 機器人 Python 版本

## 公告

## 近期變動
### 1.5.ν (2024 年 1 月 30 日)
![t2i](assets/preview/1.5.ν.png)
### 重要變更
- 新增Audio.py、Image.py

### 新增功能
- !AudioInfo 附上聲音檔 - 查看音樂資訊並顯示波型
- !AudioReverse 附上聲音檔 - 反轉聲音檔
- !AudioSpeed [倍速] 附上聲音檔 - 調整聲音速度
- !AudioBit [位元] 附上聲音檔 - 調整聲音位元
- !Sharpen [1~100的整數] 附上圖片 - 調整銳化程度
- !Blur [1~100的整數] 附上圖片 - 調整模糊程度
- !Mosaic [整數] 附上圖片 - 套上馬賽克效果
- !Brightness [0~100的整數] 附上圖片 - 調整亮度
- !Contrast [0~100的整數] 附上圖片 - 調整對比度
- !Color [0~100的整數] 附上圖片 - 調整飽和度
- !Icon [透明度(0~100的整數)] 附上圖片 - 添加浮水印

### 已知問題
- N/A
  
### 1.5.μ (2024 年 1 月 9 日)
![t2i](assets/preview/1.5.μ.png)
### 重要變更
- 刪除了Music.py改為Youtube.py(不再支持streetvoice)，修正了Youtube 複數影片清單無法播放及Youtube 無法累加播放清單的問題
- 修正了並且改善了!Help - 幫助訊息過長無法傳出的問題

### 新增功能
- !List - 長門櫻顯示撥放清單
- !Skip [數字] - 跳過 [數字] 首歌

### 已知問題
- N/A 

### 1.5.λ (2024 年 1 月 3 日)
![t2i](assets/preview/1.5.λ.png)
### 重要變更
- AutoReply.py 升級為 AutoReply_v2.py 改為使用小型分類模型來回覆使用者，大幅提升可靠度
- 新增beta分類以及新增main_beta.py，能更直觀的看出哪些是測試功能哪些是一般功能
- 統一外掛 cogs 及 beta 的格式，更改代碼更舒服了

### 新增功能
- !Version - 顯示當前機器人版本

### 已知問題
- !play [網址] - Youtube 複數影片清單無法播放
- !play [網址] - Youtube 無法累加播放清單
- !Help - 幫助訊息過長無法傳出

### 1.5.κ (2024 年 1 月 1 日)
![t2i](assets/preview/1.5.κ.png)
### 重要變更
- TAG 長門櫻 並且附加檔案上去後，長門櫻會自動把檔案下載到運行伺服器上 (Beta)

### 新增功能
- !CheckSMS [文字] - 自製小型AI模型判斷簡訊類別 (模型版本 : Project SMS Model 50)
- !GenerateBarCode [12位數字] - 生成EAN13條碼
- !GenerateQRCode [內容] [數字] - 生成QRCode，數字決定QRCode造型可有可無
- !GenerateQRCode [內容] [數字] [附加圖片] - 生成崁入圖片的QRCode
- !VideoToGif [附加影片檔] [寬] [高] [起始時間] [結束時間] [幀數] - 將影片生成Gif檔
- !PingIP [網址] - 查詢網站 IP

### 已知問題
- !play [網址] - Youtube 複數影片清單無法播放
- !play [網址] - Youtube 無法累加播放清單
- !Help - 幫助訊息過長無法傳出


### 1.5.ι (2023 年 12 月 22 日)
![t2i](assets/preview/1.5.ι.png)
### 重要變更
- 首個對外公開的版本
- 調整伺服器資料的儲存方式 (存放方式改為將資料存到server/伺服器ID/資料伺服器ID.json)
- 重製等級系統，所有等級歸0，大幅降低每等所需經驗值 (原本6等級^4/2.5改為6等級^2/2.5)

### 新增功能
- !VoteCreate [問題] [選項1] [選項2] [選項N] - 創建投票
- !Vote [問題] [選項名稱] - 投票
- !VoteResult [問題] - 顯示投票結果
- !join - 機器人進入語音聊天室
- !leave - 機器人離開語音聊天室 
- !play [網址] - 播放音樂(目前支援以下平台:StreetVoice，Youtube)
- !GuessingGameStart - 開啟猜數字遊戲
- !Guess [數字] - 猜數字
- !Tarot - 抽塔羅牌
- !PrimeNumber [整數] - 判斷是否為質數
- !Greeting [文字] - 自製小型AI模型判斷文字是否為打招呼 (模型版本 : Project Hello Model 500)

### 已知問題
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
 ```shell
- pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
- NVIDIA GPU驅動程式
- 下載: https://www.nvidia.com/zh-tw/geforce/drivers/
- NVIDIA CUDA Toolkit
- 下載: https://developer.nvidia.com/cuda-toolkit
- NVIDIA cuDNN
- 下載: https://developer.nvidia.com/cudnn
- **FFMPEG**
- 下載: https://ffmpeg.org/download.html
```shell
py -3 -m pip install -U discord.py
py -3 -m pip install -U discord.py[voice]
pip install numpy
pip install numexpr
pip install googletrans==3.1.0a0
pip install requests
pip install openai
pip install youtube_dl
pip install Pillow==9.5.0
pip install beautifulsoup4
pip install --upgrade httpcore
pip install moviepy
pip install ffmpeg
pip install qrcode
pip install python-barcode
pip install matplotlib
```
### 環境變數
```shell
C:\Program Files\ffmpeg-master-latest-win64-gpl\bin
```
### youtube_dl修復
1. 尋找youtube-dl中的youtube.py
Microsoft Store 版本路徑
```shell
"C:\Users\使用者名稱\AppData\Local\Packages\PythonSoftwareFoundation.<Python版本>\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
```
一般版本路徑
```shell
"C:\Users\使用者名稱\AppData\Local\Programs\Python\<Python版本>\Lib\site-packages\youtube_dl\extractor\youtube.py"
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
Microsoft Store 版本路徑
```shell
"C:\Users\使用者名稱\AppData\Local\Packages\PythonSoftwareFoundation.<Python版本>\LocalCache\local-packages\Python310\site-packages\googletrans\client.py"
```
一般版本路徑
```shell
"C:\Users\使用者名稱\AppData\Local\Programs\Python\<Python版本>\Lib\site-packages\googletrans\client.py"
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
