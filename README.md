# Nagato-Sakura-Discord-Bot-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)
[![GitHub release](https://img.shields.io/github/v/release/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/releases)

\[ 中文 | [English](README_en.md) | [日本語](README_jp.md) \]

## 介紹
Nagato-Sakura-Discord-Bot-py 是「長門櫻計畫」的其中一個分支，是以 Python 撰寫的多功能 Discord 機器人

## 公告
- ### 1.6.2 版本將對 cogs 進行大幅度整合，刪除重複度高的 cogs 並將類似功能的 cogs 整合在一起，這樣可以大幅縮短擴展的加載時間。
- ### 1.6.2 版本將對資產進行調整，將原本的 png 改為 jpg 大幅減少了儲存庫容量並且提升了部分程式在 discord 的回應速度。

## 近期變動
### 1.6.1 (2024 年 2 月 26 日)
![t2i](assets/preview/1.6.1.jpg)
### 重要變更
- N/A
### 新增功能
- 【新增】!FacialFeaturesDetection 附上圖片 - 五官偵測標記
- 【新增】!FacialFeaturesDetectMultiScale 附上圖片 - 五官偵測並標記(眼睛綠色方框、嘴巴紅色方框、鼻子藍色方框)
- 【新增】!SuperDeformed - 可以隨機抽取長門櫻的Q版圖片。
- 【更新】Choices.py、CustomCommands.py、Level.py、Translate.py、Version.py及Weather.py新增了/指令。
- 【更新】!CheckSMS [文字] - 更新模型版本，現在可以判斷簡訊的類別、簡訊中的電話、簡訊中的網址並且能檢測網址的安全性。
- 【測試】!SnakeGame - 玩貪吃蛇遊戲，!SnakeGameReset - 重置貪吃蛇遊戲。
### 已知問題
- N/A

### 1.6.0 (2024 年 2 月 17 日)
![t2i](assets/preview/1.6.0.jpg)
### 重要變更
- 【重大】main_beta.py 新增了 載入指令程式檔案、卸載指令檔案、重新載入程式檔案、載入斜線指令。
- 【調整】大幅精簡了部分程式的行數，並且提高了程式的效率。
### 新增功能
- 【新增】!FestivalEvent - 當特殊的日子來臨之時會有彩蛋。
- 【更新】DM.py 及 Tarot.py 新增了/指令。
### 已知問題
- 【錯誤】!Tarot - 無法產生正確圖片及正逆為牌意。

### 1.5.ν (2024 年 1 月 30 日)
![t2i](assets/preview/1.5.ν.jpg)
### 重要變更
- N/A
### 新增功能
- 【新增】!AudioInfo 附上聲音檔 - 查看音樂資訊並顯示波型。
- 【新增】!AudioReverse 附上聲音檔 - 反轉聲音檔。
- 【新增】!AudioSpeed [倍速] 附上聲音檔 - 調整聲音速度。
- 【新增】!AudioBit [位元] 附上聲音檔 - 調整聲音位元。
- 【新增】!Sharpen [1~100的整數] 附上圖片 - 調整銳化程度。
- 【新增】!Blur [1~100的整數] 附上圖片 - 調整模糊程度。
- 【新增】!Mosaic [整數] 附上圖片 - 套上馬賽克效果。
- 【新增】!Brightness [0~100的整數] 附上圖片 - 調整亮度。
- 【新增】!Contrast [0~100的整數] 附上圖片 - 調整對比度。
- 【新增】!Color [0~100的整數] 附上圖片 - 調整飽和度。
- 【新增】!Icon [透明度(0~100的整數)] 附上圖片 - 添加浮水印。
### 已知問題
- N/A

## 快速開始
 **粗體** 的是強制要求的。

### 系統需求
- 系統需求: 64-bit Windows
- **處理器**: 64 位元的處理器
- **記憶體**: 2GB
- 顯示卡: 1GB VRAM 且支援 CUDA 加速的 NVIDIA 顯示卡
- **儲存空間**: 3GB 可用空間

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
pip install dlib
pip install opencv-python
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

## 待辦事項
- [ ] **高優先度：**
  - [x] 用户指南。
  - [x] 整合重複或的相似功能。
  - [x] 調整資產。

- [ ] **功能:**
  - 整合/指令
    - [ ] Audio.py
    - [ ] CheckSMS.py (檢查網址會導致程式超時，暫時跳過添加/指令)
    - [x] Choices.py
    - [x] CustomCommands.py
    - [x] Del.py
    - [X] Dice.py
    - [x] DM.py
    - [ ] FestivalEvent.py
    - [ ] GenerateCode.py
    - [ ] Game.py
    - [x] Help.py
    - [ ] Image.py
    - [x] Level.py
    - [x] Math.py
    - [X] Ping.py
    - [x] Tarot.py
    - [x] Translate.py
    - [x] Version.py
    - [ ] Video.py
    - [x] Vote.py
    - [x] Weather.py
    - [ ] Youtube.py
     
## 致謝
特別感謝以下項目和貢獻者：

- [dlib-models](https://github.com/davisking/dlib-models)
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [moviepy](https://github.com/Zulko/moviepy)
- [node-opencv](https://github.com/peterbraden/node-opencv)
- [numexpr](https://github.com/pydata/numexpr)
- [opencv-python](https://github.com/opencv/opencv-python)
- [py-googletrans](https://github.com/ssut/py-googletrans)
- [pydub](https://github.com/jiaaro/pydub)
- [python-qrcode](https://github.com/lincolnloop/python-qrcode)
- [requests](https://github.com/psf/requests)
- [youtube-dl](https://github.com/ytdl-org/youtube-dl)

## 感謝所有貢獻者的努力

<a href="https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=AmanoShizukikun/Nagato-Sakura-Discord-Bot-py" />
</a>
