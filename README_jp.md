# Discord-Bot-Nagato-Sakura-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py?style=social)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py)](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/commits/main)

\[ [中文](README.md) | [English](README_en.md) | 日本語 \]

## 介紹
Nagato-Sakura-Discord-Bot-py は「長門桜計画」の一部で、Pythonで書かれた多機能Discordボットです。

## 公告

## 最近の変更
### 1.6.0 (2024年2月17日)
![t2i](assets/preview/1.6.0.png)
### 主な変更点
- DM.pyおよびTarot.pyに / コマンドが追加され、コマンドの呼び出しがより直感的になりました。
- main_beta.pyにコマンドファイルのロード、コマンドファイルのアンロード、コマンドファイルの再ロード、スラッシュコマンドのロードが追加されました。
- 一部のプログラムの行数を削減して効率を向上させました。
### 新機能
- !FestivalEvent - 特別な日にちが来るとイースターエッグが表示されます。
### 既知の問題
- !Tarot - 正しい画像を生成できず、正逆が牌意に反映されない

### 1.5.ν (2024年1月30日)
![t2i](assets/preview/1.5.ν.png)
### 主な変更点
- Audio.py、Image.pyが追加されました。
### 新機能
- !AudioInfo [音声ファイルを添付] - 音楽情報を表示して波形を表示します。
- !AudioReverse [音声ファイルを添付] - 音声ファイルを逆再生します。
- !AudioSpeed [倍速] [音声ファイルを添付] - 音声速度を調整します。
- !AudioBit [ビット] [音声ファイルを添付] - 音声ビットを調整します。
- !Sharpen [1〜100の整数] [画像を添付] - シャープネスを調整します。
- !Blur [1〜100の整数] [画像を添付] - ぼかし度を調整します。
- !Mosaic [整数] [画像を添付] - モザイク効果を追加します。
- !Brightness [0〜100の整数] [画像を添付] - 明るさを調整します。
- !Contrast [0〜100の整数] [画像を添付] - コントラストを調整します。
- !Color [0〜100の整数] [画像を添付] - 彩度を調整します。
- !Icon [透明度(0〜100の整数)] [画像を添付] - 透かしを追加します。
### 既知の問題
- なし
  
### 1.5.μ (2024年1月9日)
![t2i](assets/preview/1.5.μ.png)
### 主な変更点
- Music.pyを削除し、Youtube.pyに変更しました（StreetVoiceはサポートされなくなりました）。複数のYouTubeビデオプレイリストを再生できない問題や、YouTubeプレイリストを追加できない問題を修正しました。
- !Help - ヘルプメッセージが長すぎて送信できない問題を修正および改善しました。
### 新機能
- !List - プレイリストを表示します。
- !Skip [数字] - [数字]曲スキップします。
### 既知の問題
- なし

### 1.5.λ (2024年1月3日)
![t2i](assets/preview/1.5.λ.png)
### 主な変更点
- AutoReply.pyがAutoReply_v2.pyにアップグレードされ、ユーザーに返信するために小規模な分類モデルが使用され、信頼性が大幅に向上しました。
- ベータ分類とmain_beta.pyが追加され、どれがテスト機能でどれが通常の機能かがより直感的にわかります。
- プラグインcogsとベータのフォーマットを統一し、コードの変更がより快適になりました。
### 新機能
- !Version - 現在のボットのバージョンを表示します。
### 既知の問題
- !play [URL] - YouTube複数のビデオプレイリストを再生できません
- !play [URL] - YouTubeプレイリストを追加できません
- !Help - ヘルプメッセージが長すぎて送信できません

### 1.5.κ (2024年1月1日)
![t2i](assets/preview/1.5.κ.png)
### 主な変更点
- 長門桜をタグ付けし、ファイルを添付した場合、長門桜は自動的にファイルを実行中のサーバーにダウンロードします（ベータ版）。
### 新機能
- !CheckSMS [テキスト] - SMSカテゴリを判別するためのカスタム小規模AIモデル（モデルバージョン：プロジェクトSMSモデル50）
- !GenerateBarCode [12桁の数字] - EAN13バーコードを生成します。
- !GenerateQRCode [内容] [数字] - QRコードを生成し、数字でQRコードのスタイルを含めるかどうかを決定します。
- !GenerateQRCode [内容] [数字] [追加画像] - 画像を埋め込んだQRコードを生成します。
- !VideoToGif [ビデオファイル] [幅] [高さ] [開始時間] [終了時間] [フレームレート] - ビデオをGifファイルに変換します。
- !PingIP [URL] - ウェブサイトのIPを調べます。
### 既知の問題
- !play [URL] - YouTube複数のビデオプレイリストを再生できません
- !play [URL] - YouTubeプレイリストを追加できません
- !Help - ヘルプメッセージが長すぎて送信できません


### 1.5.ι (2023年12月22日)
![t2i](assets/preview/1.5.ι.png)
### 主な変更点
- 初の公開リリース
- サーバーデータの保存方法を調整しました（データをserver/server ID/data server ID.jsonに保存するように変更）
- レベルシステムをリセットし、すべてのレベルを0にリセットし、必要な経験値を大幅に減らしました（以前は6レベル^4/2.5から6レベル^2/2.5に変更）
### 新機能
- !VoteCreate [質問] [オプション1] [オプション2] [オプションN] - 投票を作成します。
- !Vote [質問] [オプション名] - 投票します。
- !VoteResult [質問] - 投票結果を表示します。
- !join - ボットがボイスチャットルームに参加します。
- !leave - ボットがボイスチャットルームから退出します。
- !play [URL] - 音楽を再生します（現在、StreetVoice、Youtubeなどのプラットフォームをサポートしています）。
- !GuessingGameStart - 推測ゲームを開始します。
- !Guess [数字] - 数字を推測します。
- !Tarot - タロットカードを引きます。
- !PrimeNumber [整数] - 素数かどうかを判定します。
- !Greeting [テキスト] - カスタム小規模AIモデルを使用してテキストが挨拶かどうかを判定します（モデルバージョン：Project Hello Model 500）。
### 既知の問題
- !play [URL] - YouTube複数のビデオプレイリストを再生できません
- !play [URL] - YouTubeプレイリストを追加できません


## はじめに
 **太字** は必須の要件です。


### ハードウェア要件
1. オペレーティングシステム：Windows
2. **CPU** / Nvidia GPU


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

