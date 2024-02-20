# Discord-Bot-Nagato-Sakura-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)
[![GitHub release](https://img.shields.io/github/v/release/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/releases)

\[ [中文](README.md) | English  | [日本語](README_jp.md) \]

## Introduction
Nagato-Sakura-Discord-Bot-py is one of the branches of the "Nagato-Sakura Project," a multifunctional Discord bot written in Python.


## Announcements


## Recent Changes
### 1.6.0 (February 17, 2024)
![t2i](assets/preview/1.6.0.png)
#### Important Changes
- Added `/` commands to `DM.py` and `Tarot.py`, improving the intuitiveness of command invocation.
- Enhanced `main_beta.py` with functionalities such as loading command program files, unloading command files, reloading program files, and loading slash commands.
- Optimized code in certain areas to improve efficiency.
#### New Features
- !FestivalEvent - Easter eggs for special occasions
#### Known Issues
- !Tarot - Unable to generate correct images and reversed card meanings

### 1.5.ν (January 30, 2024)
![t2i](assets/preview/1.5.ν.png)
### Important Changes
- Added Audio.py and Image.py
### New Features
- !AudioInfo [sound file] - View music information and display waveform
- !AudioReverse [sound file] - Reverse sound file
- !AudioSpeed [speed] [sound file] - Adjust sound speed
- !AudioBit [bitrate] [sound file] - Adjust sound bitrate
- !Sharpen [1~100 integer] [image] - Adjust sharpness
- !Blur [1~100 integer] [image] - Adjust blur
- !Mosaic [integer] [image] - Apply mosaic effect
- !Brightness [0~100 integer] [image] - Adjust brightness
- !Contrast [0~100 integer] [image] - Adjust contrast
- !Color [0~100 integer] [image] - Adjust saturation
- !Icon [transparency (0~100 integer)] [image] - Add watermark
### Known Issues
- N/A

### 1.5.μ (January 9, 2024)
![t2i](assets/preview/1.5.μ.png)
### Important Changes
- Music.py has been replaced with Youtube.py (no longer supports StreetVoice), fixing issues with playing multiple YouTube video playlists and adding playlists
- Improved and fixed the issue where !Help message was too long to send
### New Features
- !List - Display Nagato-Sakura's playlist
- !Skip [number] - Skip [number] songs
### Known Issues
- N/A

### 1.5.λ (January 3, 2024)
![t2i](assets/preview/1.5.λ.png)
### Important Changes
- Upgraded AutoReply.py to AutoReply_v2.py, utilizing a smaller classification model for user responses, significantly enhancing reliability.
- Added beta classification and introduced main_beta.py for a clearer differentiation between testing and regular functionalities.
- Unified the format for plugins under 'cogs' and beta, making code modifications more comfortable.
### New Features
- !Version - Displays the current bot version.
### Known Issues
- !play [URL] - Unable to play multiple video playlists from YouTube.
- !play [URL] - Unable to queue YouTube playlist items.
- !Help - Inability to send out help messages due to excessive length.

### 1.5.κ (January 1, 2024)
![t2i](assets/preview/1.5.κ.png)
### Important Changes
- TAG Nagato Sakura and after attaching the file, Nagato Sakura will automatically download the file to the running server (Beta)
### New Features
- !CheckSMS [Text] - Self-made small AI model to determine the message category (Model version: Project SMS Model 50)
- !GenerateBarCode [12 digits] - Generate EAN13 barcode
- !GenerateQRCode [content] [number] - Generate QRCode, the number determines whether the QRCode shape is optional
- !GenerateQRCode [Content] [Number] [Additional Image] - Generate QRCode embedded in the image
- !VideoToGif [Attach video file] [Width] [Height] [Start time] [End time] [Frame number] - Generate video into Gif file
### Known issues
- !play [URL] - Youtube multiple video list cannot be played
- !play [url] - Youtube cannot accumulate playlists

- ### 1.5.ι (December 22, 2023)
![t2i](assets/preview/1.5.ι.png)
### Important Changes
- The first public version
- Adjust the storage method of server data (the storage method is changed to save data to server/server ID/data server ID.json)
- Reworked the level system, all levels are reset to 0, and the experience points required for each level are greatly reduced (original level 6^4/2.5 is changed to level 6^2/2.5)
### New Features
- !VoteCreate [Question] [Option 1] [Option 2] [Option N] - Create a vote
- !Vote [question] [option name] - Vote
- !VoteResult [question] - displays the vote results
- !join - the robot enters the voice chat room
- !leave - the bot leaves the voice chat room
- !play [Website] - Play music (currently supports the following platforms: StreetVoice, Youtube)
- !GuessingGameStart - Start the guessing game
- !Guess [Number] - Guess the number
- !Tarot - draw tarot cards
- !PrimeNumber [integer] - Determine whether it is a prime number
- !Greeting [Text] - Self-made small AI model to determine whether the text is a greeting (Model version: Project Hello Model 500)
### Known issues
- !play [URL] - Youtube multiple video list cannot be played
- !play [url] - Youtube cannot accumulate playlists


## Quick start
  **Bold** are mandatory.
 
### Hardware requirements
1. Operating system: Windows
1. **CPU** / Nvidia GPU

### Environment settings
- **Python 3**
- Download: https://www.python.org/downloads/windows/
- **PyTorch**
- Download: https://pytorch.org/
- NVIDIA GPU driver
- Download: https://www.nvidia.com/zh-tw/geforce/drivers/
- NVIDIA CUDA Toolkit
- Download: https://developer.nvidia.com/cuda-toolkit
- NVIDIA cuDNN
- Download: https://developer.nvidia.com/cudnn
- **FFMPEG**
- Download: https://ffmpeg.org/download.html
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
### Environment variables
```shell
C:\Program Files\ffmpeg-master-latest-win64-gpl\bin
```
### youtube_dl fix
1. Find youtube.py in youtube-dl
```shell
"C:\Users\username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
```
2. Modify youtube.py and modify line 1794:
```shell
'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
direct annotation
```shell
#'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
3. Save youtube.py

### Translate.py fix (new bug after Google update in November)
1. Find client.py in googletrans
```shell
"C:\Users\username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\googletrans\client.py"
```
2. Modify client.py and modify line 57:
```shell
proxies: typing.Dict[str, httpcore.SyncHTTPTransport] = None,
```
Change to
```shell
proxies: typing.Dict[str, httpcore.AsyncHTTPProxy] = None,
```
3. Save client.py
