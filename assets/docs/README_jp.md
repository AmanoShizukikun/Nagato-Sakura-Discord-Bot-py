# Discord-Bot-Nagato-Sakura-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)
[![GitHub release](https://img.shields.io/github/v/release/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/releases)

\[ [中文](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/README.md) | [English](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/docs/README_en.md) | 日本語 \]

## 介紹
Nagato-Sakura-Discord-Bot-py は「長門桜計画」の一部で、Pythonで書かれた多機能Discordボットです。

## 公告
- ### バージョン1.6.2では、cogsを大幅に統合し、重複度の高いcogsを削除し、類似した機能のcogsを一緒に統合することで、拡張の読み込み時間を大幅に短縮することができます。
- ### バージョン1.6.2では、アセットを調整し、元々のpngをjpgに変更することで、リポジトリのサイズを大幅に減少させ、一部のプログラムのdiscordでの応答速度を向上させました。

## 最近の変更
### 1.6.2 (2024年3月1日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.2.jpg)
### 重要な変更
- 【重要】リポジトリのファイルを整理し、一部の説明書をassets/docsに移動しました。
- 【重要】アセットの調整。pngからjpgに変更することで、リポジトリの容量が大幅に削減され、一部のプログラムのdiscordでの応答速度が向上しました。
- 【重要】Del.pyをbetaに移動。一般モードでの悪用を避けるため、削除権限が高すぎると個人的に考えられるためです。
- 【統合】Game.pyにGuessingGame.pyとSnakeGame.pyを統合し、今後のゲーム関連の機能はすべてここに統合されます。
- 【統合】Image.pyにImage.pyとSuperDeformed.pyを統合し、今後の画像関連の機能はすべてここに統合されます。
- 【統合】Math.pyにMath.pyとPrimeNumber.pyを統合し、今後の計算関連の機能はすべてここに統合されます。
- 【削除】!Userinfo [ユーザー名] - !Level機能と類似しているため、削除されました。
- 【削除】!Greeting [テキスト] - このプログラムはAutoReply.pyの前身であり、役割を完了したため、削除されました。
### 新機能
- 【更新】Del.py、Dice.py、Help.py、Ping.py、Vote.py、Youtube.pyに/コマンドが追加されました。
- 【更新】Version.py - 新しいアセットの出力形式に更新されました。
- 【更新】Help.py - ボタンを削除し、埋め込みコンテンツを再書き込みました。
- 【更新】FestivalEvent.py - より多くのイースターエッグコンテンツが追加されました。
- 【更新】CheckSMS.py - 驗證コードのテキストメッセージを検出し、コードを出力し、モデルのバージョンが更新されました。[ブランチプロジェクトの詳細はこちら](https://github.com/AmanoShizukikun/Nagato-Sakura-SMS-Checker/blob/main/assets/docs/Changelog.md#1042024-%E5%B9%B4-3-%E6%9C%88-1-%E6%97%A5)
- 【修正】CheckSMS.py - 小数点を含むメッセージを誤ってURLとして認識する問題が修正されました。
### 既知の問題
- 【エラー】Youtube.pyの/play [URL]コマンドを使用すると、再生リストの場合にタイムアウトエラーが高確率で発生します。プログラムのタイムアウトによるエラーを回避するため、再生リストを使用する場合は!Play [URL]を使用することをお勧めします。

### 1.6.1 (2024年2月26日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.1.jpg)
### 重要な変更
- N/A
### 新機能
- 【新規】!FacialFeaturesDetection 画像を添付して - 顔の特徴を検出し、マーキングします
- 【新規】!FacialFeaturesDetectMultiScale 画像を添付して - 顔の特徴を検出し、マーキングします（緑の枠で目、赤の枠で口、青の枠で鼻）
- 【新規】!SuperDeformed - 長門サクラのチビ画像をランダムに選択できます。
- 【新規】Choices.py、CustomCommands.py、Level.py、Translate.py、Version.py、Weather.pyに/コマンドが追加されました。
- 【更新】!CheckSMS [テキスト] - モデルのバージョンが更新され、テキストメッセージの種類、電話番号、およびURLを検出し、URLの安全性を確認できるようになりました。
- 【テスト】!SnakeGame - スネークゲームをプレイします。!SnakeGameReset - スネークゲームをリセットします。
### 既知の問題
- N/A

### 1.6.0 (2024年2月17日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.6.0.jpg)
### 重要な変更
- 【重要】main_beta.pyに、コマンドファイルのロード、アンロード、再ロード、およびスラッシュコマンドのロードが追加されました。
- 【調整】一部のプログラムの行数を大幅に削減し、プログラムの効率を向上させました。
### 新機能
- 【新規】!FestivalEvent - 特別な日にイースターエッグが表示されます。
- 【更新】DM.pyとTarot.pyに/コマンドが追加されました。
### 既知の問題
- 【エラー】!Tarot - 正しい画像を生成できず、正逆のカードの意味がわかりません。

[すべてのリリースバージョン](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/docs/Changelog.md)

## クイックスタート
 **太字** は必須項目です。
### システム要件
- システム要件: 64ビットWindows
- **プロセッサー**: 64ビットプロセッサー
- **メモリ**: 2GB
- グラフィックスカード: 1GB VRAM およびCUDAアクセラレーションをサポートするNVIDIAグラフィックスカード
- **ストレージ**: 3GBの空き容量

### 環境のセットアップ
- **Python 3**
  - ダウンロード: [Python](https://www.python.org/downloads/windows/)
- **PyTorch**
  - ダウンロード: [PyTorch](https://pytorch.org/)
- NVIDIA GPUドライバ
  - ダウンロード: [NVIDIA Drivers](https://www.nvidia.com/zh-tw/geforce/drivers/)
- NVIDIA CUDA Toolkit
  - ダウンロード: [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
- NVIDIA cuDNN
  - ダウンロード: [cuDNN](https://developer.nvidia.com/cudnn)
- **FFMPEG**
  - ダウンロード: [FFMPEG](https://ffmpeg.org/download.html)
- Python
```shell
python3 -m pip install -U discord.py
python3 -m pip install -U discord.py[voice]
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

### 環境変数
```shell
C:\Program Files\ffmpeg-master-latest-win64-gpl\bin
```

### youtube_dl修復
1. youtube-dlのyoutube.pyを見つける
Microsoft Store版のパス
```shell
"C:\Users\ユーザー名\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
```
一般版のパス
```shell
"C:\Users\ユーザー名\AppData\Local\Programs\Python\<Pythonバージョン>\Lib\site-packages\youtube_dl\extractor\youtube.py"
```
2. youtube.pyを編集し、1794行目を修正:
```shell
'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
コメントアウト
```shell
#'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
3. youtube.pyを保存

### Translate.py修復（11月のGoogle更新後の新しいエラー）
1. Googletransのclient.pyを探す
Microsoft Store版のパス
```shell
"C:\Users\ユーザー名\AppData\Local\Packages\PythonSoftwareFoundation.<Pythonバージョン>\LocalCache\local-packages\Python310\site-packages\googletrans\client.py"
```
一般版のパス
```shell
"C:\Users\ユーザー名\AppData\Local\Programs\Python\<Pythonバージョン>\Lib\site-packages\googletrans\client.py"
```
2. client.pyを編集し、57行目を変更:
```shell
proxies: typing.Dict[str, httpcore.SyncHTTPTransport] = None,
```
以下に変更
```shell
proxies: typing.Dict[str, httpcore.AsyncHTTPProxy] = None,
```
3. client.pyを保存

## タスクリスト
- [ ] **高優先度：**
  - [x] ユーザーガイド。
  - [x] 重複した機能の統合。
  - [x] アセットの調整。

- [ ] **機能:**
  - 統合/コマンド
    - [ ] Audio.py
    - [ ] CheckSMS.py (URLのチェックはプログラムのタイムアウトを引き起こす可能性があります)
    - [ ] FestivalEvent.py
    - [ ] GenerateCode.py
    - [ ] Game.py
    - [ ] Image.py
    - [ ] Video.py
     
## 謝辞
以下のプロジェクトと貢献者に特別な感謝を申し上げます：

### プロジェクト
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

### 貢献者
<a href="https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=AmanoShizukikun/Nagato-Sakura-Discord-Bot-py" />
</a>

