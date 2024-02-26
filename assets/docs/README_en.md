# Discord-Bot-Nagato-Sakura-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)
[![GitHub release](https://img.shields.io/github/v/release/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/releases)

\[ [中文](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/README.md) | English  | [日本語](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/docs/README_jp.md) \]

## Introduction
Nagato-Sakura-Discord-Bot-py is one of the branches of the "Nagato-Sakura Project," a multifunctional Discord bot written in Python.


## Announcements

## Recent Changes
### 1.6.1 (February 26, 2024)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.1.jpg)
### Major Changes
- N/A
### New Features
- [New] !SuperDeformed - Randomly fetches chibi images of Nagato Sakura.
- [Updated] Choices.py, CustomCommands.py, Level.py, Translate.py, Version.py, and Weather.py added / commands.
- [Updated] !CheckSMS [text] - Updated model version, now capable of identifying SMS category, phone numbers in SMS, URLs in SMS, and checking URL safety.
- [Beta] !SnakeGame - Play the snake game, !SnakeGameReset - Reset the snake game.
### Known Issues
- N/A

### 1.6.0 (February 17, 2024)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.0.jpg)
### Major Changes
- [Major] main_beta.py added functionality for loading command scripts, unloading command files, reloading program files, loading slash commands.
- [Adjustment] Drastically reduced the number of lines in some scripts and improved program efficiency.
### New Features
- [New] !FestivalEvent - Special events on specific days.
- [Updated] DM.py and Tarot.py added / commands.
### Known Issues
- [Error] !Tarot - Unable to generate correct images and incorrect interpretation of upright and reverse meanings.

### 1.5.ν (January 30, 2024)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.5.%CE%BD.jpg)
### Major Changes
- N/A
### New Features
- [New] !AudioInfo with audio file - View music information and display waveform.
- [New] !AudioReverse with audio file - Reverse audio file.
- [New] !AudioSpeed [speed] with audio file - Adjust audio speed.
- [New] !AudioBit [bitrate] with audio file - Adjust audio bitrate.
- [New] !Sharpen [1~100 integer] with image - Adjust sharpness.
- [New] !Blur [1~100 integer] with image - Adjust blur.
- [New] !Mosaic [integer] with image - Apply mosaic effect.
- [New] !Brightness [0~100 integer] with image - Adjust brightness.
- [New] !Contrast [0~100 integer] with image - Adjust contrast.
- [New] !Color [0~100 integer] with image - Adjust saturation.
- [New] !Icon [opacity (0~100 integer)] with image - Add watermark.
### Known Issues
- N/A

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

## To-Do List
- [ ] **High Priority:**
  - [x] User guide.

- [ ] **Features:**
  - Integration/Commands
    - [ ] Audio.py
    - [ ] CheckSMS.py
    - [x] Choices.py
    - [x] CustomCommands.py
    - [ ] Del.py
    - [ ] Dice.py
    - [x] DM.py
    - [ ] FestivalEvent.py
    - [ ] GenerateCode.py
    - [ ] Greeting.py
    - [ ] GuessingGame.py
    - [ ] Help.py
    - [ ] Image.py
    - [x] Level.py
    - [x] Math.py
    - [ ] Ping.py
    - [ ] PrimeNumber.py
    - [ ] SuperDeformed.py
    - [x] Tarot.py
    - [x] Translate.py
    - [ ] Userinfo.py
    - [x] Version.py
    - [ ] VideoToGif.py
    - [ ] Vote.py
    - [x] Weather.py
    - [ ] Youtube.py
     
## Acknowledgements
Special thanks to the following projects and contributors:

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

## Thanks to all contributors for their efforts

<a href="https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=AmanoShizukikun/Nagato-Sakura-Discord-Bot-py" />
</a>
