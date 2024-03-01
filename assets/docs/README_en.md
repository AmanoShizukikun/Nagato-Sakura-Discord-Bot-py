# Discord-Bot-Nagato-Sakura-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)
[![GitHub release](https://img.shields.io/github/v/release/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/releases)

\[ [中文](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/README.md) | English  | [日本語](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/docs/README_jp.md) \]

## Introduction
Nagato-Sakura-Discord-Bot-py is one of the branches of the "Nagato-Sakura Project," a multifunctional Discord bot written in Python.

## Announcements
- ### Version 1.6.2 will significantly integrate cogs, remove highly redundant cogs, and merge cogs with similar functions together, greatly reducing the loading time of extensions.
- ### Version 1.6.2 will adjust assets, changing PNG to JPG significantly reducing repository size and improving the response speed of some programs on Discord.

## Recent Changes
### 1.6.2 (March 1, 2024)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.2.jpg)
### Important Changes
- [Critical] Repository files reorganized, some documentation moved to assets/docs.
- [Critical] Asset adjustments, changed PNG to JPG significantly reducing repository size and improving response speed of some programs on Discord.
- [Critical] Del.py moved to beta - Due to excessive deletion permissions, it's deemed inappropriate for general use to prevent misuse.
- [Integration] Game.py integrated GuessingGame.py and SnakeGame.py, all game-related functions will now be integrated here.
- [Integration] Image.py integrated Image.py and SuperDeformed.py, all image-related functions will now be integrated here.
- [Integration] Math.py integrated Math.py and PrimeNumber.py, all calculation-related functions will now be integrated here.
- [Removed] !Userinfo [username] - Removed due to similarity with !Level function.
- [Removed] !Greeting [text] - This program was the precursor judged by AutoReply.py, it has completed its mission perfectly and it's time to let it go.
### New Features
- [Update] Del.py, Dice.py, Help.py, Ping.py, Vote.py, and Youtube.py added / commands.
- [Update] Version.py - Updated to output format compatible with the new asset.
- [Update] Help.py - Removed buttons and rewrote embedded content.
- [Update] FestivalEvent.py - Added more easter egg content.
- [Update] CheckSMS.py - Now capable of identifying verification code SMS and outputting the code, and updated model version. [See branch project for details](https://github.com/AmanoShizukikun/Nagato-Sakura-SMS-Checker/blob/main/assets/docs/Changelog.md#1042024-%E5%B9%B4-3-%E6%9C%88-1-%E6%97%A5)
- [Fix] CheckSMS.py - Fixed error where messages with decimals were mistakenly identified as URLs.
### Known Issues
- [Error] Youtube.py using the /play [URL] command, if it's a playlist, there is a high chance of error (timeout), it is recommended to use !Play [URL] when playing playlists to avoid program errors due to timeouts.

### 1.6.1 (February 26, 2024)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.1.jpg)
### Important Changes
- N/A
### New Features
- [New] !FacialFeaturesDetection with image - Facial feature detection markers
- [New] !FacialFeaturesDetectMultiScale with image - Facial feature detection and markers (green box for eyes, red box for mouth, blue box for nose)
- [New] !SuperDeformed - Can randomly draw chibi pictures of Nagato Sakura.
- [New] Choices.py, CustomCommands.py, Level.py, Translate.py, Version.py, and Weather.py added / commands.
- [Update] !CheckSMS [text] - Updated model version, can now determine SMS category, phone number in SMS, URLs in SMS, and can detect URL security.
- [Test] !SnakeGame - Play Snake game, !SnakeGameReset - Reset Snake game.
### Known Issues
- N/A

### 1.6.0 (February 17, 2024)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.0.jpg)
### Important Changes
- [Critical] main_beta.py added Load command program file, Unload command file, Reload program file, Load slash commands.
- [Adjustment] Substantially reduced the number of lines in some programs and improved program efficiency.
### New Features
- [New] !FestivalEvent - Easter eggs when special days come.
- [Update] DM.py and Tarot.py added / commands.
### Known Issues
- [Error] !Tarot - Unable to generate correct images and upright and reverse meanings.

[All Releases](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/docs/Changelog.md)

## Quick Start
 **Bold** indicates mandatory.
### System Requirements
- System Requirements: 64-bit Windows
- **Processor**: 64-bit processor
- **Memory**: 2GB
- Graphics Card: 1GB VRAM NVIDIA graphics card with CUDA acceleration support
- **Storage**: 3GB available space

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
- Python
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
Microsoft Store Version Path
```shell
"C:\Users\username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
```
Regular Version Path
```shell
"C:\Users\username\AppData\Local\Programs\Python\<PythonVersion>\Lib\site-packages\youtube_dl\extractor\youtube.py"
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
Microsoft Store Version Path
```shell
"C:\Users\username\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\googletrans\client.py"
```
Regular Version Path
```shell
"C:\Users\username\AppData\Local\Programs\Python\<PythonVersion>\Lib\site-packages\googletrans\client.py"
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

## To-Do List
- [ ] **High Priority:**
  - [x] User guide.
  - [x] Integrate redundant or similar functions.
  - [x] Adjust assets.

- [ ] **Features:**
  - Integration / commands
    - [ ] Audio.py
    - [ ] CheckSMS.py (Checking URLs causes program timeout)
    - [ ] FestivalEvent.py
    - [ ] GenerateCode.py
    - [ ] Game.py
    - [ ] Image.py
    - [ ] Video.py

## Acknowledgements
Special thanks to the following projects and contributors:

### Projects
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

### Contributors
<a href="https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=AmanoShizukikun/Nagato-Sakura-Discord-Bot-py" />
</a>
