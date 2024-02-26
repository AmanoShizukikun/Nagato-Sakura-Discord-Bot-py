# Discord-Bot-Nagato-Sakura-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)
[![GitHub release](https://img.shields.io/github/v/release/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/releases)

\[ [中文](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/README.md) | [English](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/docs/README_en.md) | 日本語 \]

## 介紹
Nagato-Sakura-Discord-Bot-py は「長門桜計画」の一部で、Pythonで書かれた多機能Discordボットです。

## 公告

## 最近の変更
### 1.6.1（2024年2月26日）
![t2i](assets/preview/1.6.1.png)
### 重要な変更
- N/A
### 新機能
- 【追加】!SuperDeformed - 長門さくらのチビキャラ画像をランダムに抽出できます。
- 【更新】Choices.py、CustomCommands.py、Level.py、Translate.py、Version.py、Weather.pyに「/」コマンドを追加しました。
- 【更新】!CheckSMS [テキスト] - モデルバージョンを更新し、今ではSMSの種類、電話番号、URLの検出、およびURLの安全性を判断できます。
- 【テスト】!SnakeGame - スネークゲームをプレイします。!SnakeGameReset - スネークゲームをリセットします。
###既知の問題
- N/A

### 1.6.0（2024年2月17日）
![t2i](assets/preview/1.6.0.png)
### 重要な変更
- 【重要】main_beta.pyにコマンドファイルの読み込み、アンインストール、ファイルの再読み込み、スラッシュコマンドの追加が追加されました。
- 【調整】一部のプログラムの行数を大幅に削減し、プログラムの効率を向上させました。
### 新機能
- 【追加】!FestivalEvent - 特別な日にはイースターエッグが表示されます。
- 【更新】DM.pyおよびTarot.pyに「/」コマンドを追加しました。
### 既知の問題
- 【エラー】!Tarot - 正しい画像を生成できず、正逆がカードの意味に反映されません。

### 1.5.ν（2024年1月30日）
![t2i](assets/preview/1.5.ν.png)
### 重要な変更
- N/A
### 新機能
- 【追加】!AudioInfo - 音声ファイルを添付して音楽情報を表示し、波形を表示します。
- 【追加】!AudioReverse - 音声ファイルを逆再生します。
- 【追加】!AudioSpeed [スピード] - 音声の速度を調整します。
- 【追加】!AudioBit [ビット] - 音声のビットを調整します。
- 【追加】!Sharpen [1〜100の整数] - 画像のシャープネスを調整します。
- 【追加】!Blur [1〜100の整数] - 画像のぼかしを調整します。
- 【追加】!Mosaic [整数] - 画像にモザイク効果を適用します。
- 【追加】!Brightness [0〜100の整数] - 明るさを調整します。
- 【追加】!Contrast [0〜100の整数] - コントラストを調整します。
- 【追加】!Color [0〜100の整数] - 彩度を調整します。
- 【追加】!Icon [透明度(0〜100の整数)] - 透かしを追加します。
### 既知の問題
- N/A
  
### 1.5.μ（2024年1月9日）
![t2i](assets/preview/1.5.μ.png)
### 重要な変更
- 【重大】Music.pyを削除してYoutube.pyに変更しました（streetvoiceはサポートされなくなりました）。
### 新機能
- 【追加】!List - 長門さくらのプレイリストを表示します。
- 【追加】!Skip [番号] - [番号]曲をスキップします。
- 【修正】!Help - ヘルプメッセージが長すぎて送信されない問題を修正しました。
- 【修正】複数のYoutubeビデオリストを再生できない問題やYoutubeプレイリストを累積できない問題を修正しました。
### 既知の問題
- N/A 

### 1.5.λ（2024年1月3日）
![t2i](assets/preview/1.5.λ.png)
### 重要な変更
- 【重大】ベータカテゴリとmain_beta.pyを追加しました。テスト機能と通常の機能がより直感的に表示されるようになりました。
- 【重大】プラグインの形式を統一し、コードの変更がより快適になりました。
### 新機能
- 【追加】!Version - 現在のボットのバージョンを表示します。
- 【更新】AutoReply.pyをAutoReply_v2.pyに更新し、ユーザーに返信するために小規模な分類モデルを使用し、信頼性が大幅に向上しました。
### 既知の問題
- 【エラー】!play [URL] - Youtube複数ビデオリストが再生できません。
- 【エラー】!play [URL] - Youtubeプレイリストを累積できません。
- 【エラー】!Help - ヘルプメッセージが長すぎて送信されません。

### 1.5.κ（2024年1月1日）
![t2i](assets/preview/1.5.κ.png)
### 重要な変更
- 【重大】TAGを長門さくらに付けてファイルを添付すると、長門さくらはファイルを自動的に実行サーバーにダウンロードします。
### 新機能
- 【追加】!CheckSMS [テキスト] - 独自の小規模AIモデルを使用してSMSのカテゴリを判断します。
- 【追加】!GenerateBarCode [12桁の数字] - EAN13バーコードを生成します。
- 【追加】!GenerateQRCode [内容] [数字] - QRコードを生成します。数字はQRコードのスタイルの有無を決定します。
- 【追加】!GenerateQRCode [内容] [数字] [添付画像] - 画像を埋め込んだQRコードを生成します。
- 【追加】!VideoToGif [添付ビデオファイル] [幅] [高さ] [開始時間] [終了時間] [フレーム数] - ビデオからGIFを生成します。
- 【追加】!PingIP [URL] - ウェブサイトのIPを確認します。
### 既知の問題
- 【エラー】!play [URL] - Youtube複数ビデオリストが再生できません。
- 【エラー】!play [URL] - Youtubeプレイリストを累積できません。
- 【エラー】!Help - ヘルプメッセージが長すぎて送信されません。

### 1.5.ι（2023年12月22日）
![t2i](assets/preview/1.5.ι.png)
### 重要な変更
- 【重大】初の公開バージョン。
- 【重大】サーバーデータの保存方法を変更しました。（データをserver/サーバーID/データサーバーID.jsonに保存）
- 【重大】レベルシステムをリセットし、すべてのレベルを0に戻しました。必要な経験値が大幅に減少しました。（以前は6レベル^4/2.5から6レベル^2/2.5に変更されました）
### 新機能
- 【追加】!VoteCreate [質問] [オプション1] [オプション2] [オプションN] - 投票を作成します。
- 【追加】!Vote [質問] [オプション名] - 投票します。
- 【追加】!VoteResult [質問] - 投票結果を表示します。
- 【追加】!join - ボットが音声チャットに参加します。
- 【追加】!leave - ボットが音声チャットから退出します。
- 【追加】!play [URL] - 音楽を再生します。（現在サポートされているプラットフォーム：StreetVoice、Youtube）
- 【追加】!GuessingGameStart - 数当てゲームを開始します。
- 【追加】!Guess [数字] - 数字を推測します。
- 【追加】!Tarot - タロットカードを引きます。
- 【追加】!PrimeNumber [整数] - 素数かどうかを判断します。
- 【追加】!Greeting [テキスト] - 独自の小規模AIモデルでテキストが挨拶かどうかを判断します。
### 既知の問題
- 【エラー】!play [URL] - Youtube複数ビデオリストが再生できません。
- 【エラー】!play [URL] - Youtubeプレイリストを累積できません。

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
```shell
"C:\Users\ユーザー名\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
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
1. googletransのclient.pyを探す
```shell
"C:\Users\ユーザー名\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\googletrans\client.py"
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
- [ ] **高優先度:**
  - [x] ユーザーガイド。

- [ ] **機能:**
  - 統合/コマンド
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
     
## 謝辞
以下のプロジェクトと貢献者に特別な感謝をします：

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

## すべての貢献者に感謝します

<a href="https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=AmanoShizukikun/Nagato-Sakura-Discord-Bot-py" />
</a>
