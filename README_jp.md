# Nagato-Sakura-Discord-Bot-py

[![GitHub Repo stars](https://img.shields.io/github/stars/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py?style=social)](https://github.com/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py)](https://github.com/AmanoShizukikun/Discord-Bot-Nagato-Sakura-py/commits/main)

\[ [中文](README.md) | [English](README_en.md) | 日本語 \]

長門桜 Discord ボット Python バージョン

## お知らせ

## 最近の変更
### 1.5.ν (2024 年 1 月 30 日)
![t2i](assets/preview/1.5.ν.png)
### 重要な変更
- 新しいAudio.py、Image.pyを追加しました。

### 新機能
- !AudioInfo 音声ファイルを添付 - 音楽情報を表示し、波形を表示します。
- !AudioReverse 音声ファイルを添付 - 音声ファイルを反転させます。
- !AudioSpeed [倍速] 音声ファイルを添付 - 音声の速度を調整します。
- !AudioBit [ビット] 音声ファイルを添付 - 音声のビット深度を調整します。
- !Sharpen [1~100の整数] 画像を添付 - シャープネスを調整します。
- !Blur [1~100の整数] 画像を添付 - ぼかしの度合いを調整します。
- !Mosaic [整数] 画像を添付 - モザイク効果を適用します。
- !Brightness [0~100の整数] 画像を添付 - 明るさを調整します。
- !Contrast [0~100の整数] 画像を添付 - コントラストを調整します。
- !Color [0~100の整数] 画像を添付 - 彩度を調整します。
- !Icon [透明度(0~100の整数)] 画像を添付 - 透かしを追加します。

### 既知の問題
- N/A
  
### 1.5.μ (2024 年 1 月 9 日)
![t2i](assets/preview/1.5.μ.png)
### 重要な変更
- Music.pyを削除し、Youtube.pyに置き換えました（streetvoiceはサポートされなくなりました）。Youtubeプレイリストで複数の動画が再生できない問題や、Youtubeプレイリストを累積できない問題を修正しました。
- !Helpコマンドが過度に長いヘルプメッセージのために送信できない問題を修正および改善しました。

### 新機能
- !List - 現在の再生リストを涼宮ハルヒで表示します。
- !Skip [数字] - [数字]曲をスキップします。

### 既知の問題
- N/A
- 
### 1.5.λ（2024年1月3日）
![t2i](assets/preview/1.5.λ.png)
### 重要な変更
- AutoReply.py を AutoReply_v2.py にアップグレードし、ユーザーへの応答に小規模の分類モデルを使用して信頼性を大幅に向上させました。
- beta分類を追加し、main_beta.py を追加して、テスト機能と通常の機能をより直感的に区別できるようにしました。
- 'cogs'とbetaのプラグインの形式を統一し、コードの変更がより快適になりました。

### 新機能
- !Version - 現在のボットバージョンを表示します。

### 既知の問題
- !play [URL] - YouTubeの複数のビデオプレイリストを再生できません。
- !play [URL] - YouTubeプレイリストのアイテムをキューに入れることができません。
- !Help - 過度の長さのためヘルプメッセージを送信できません。

### 1.5.κ (2024年1月1日)
![t2i](assets/preview/1.5.κ.png)
### 重要な変更
- 長門櫻にタグを付けてファイルを添付すると、長門櫻がファイルを自動的に実行サーバーにダウンロードします（ベータ）

### 新機能
- !CheckSMS [テキスト] - 独自の小規模AIモデルでテキストメッセージのカテゴリを判別します（モデルバージョン: Project SMS Model 50）
- !GenerateBarCode [12桁の数字] - EAN13バーコードを生成します
- !GenerateQRCode [コンテンツ] [数字] - QRコードを生成し、数字でQRコードのスタイルを決定します
- !GenerateQRCode [コンテンツ] [数字] [添付画像] - 画像を埋め込んだQRコードを生成します
- !VideoToGif [添付ビデオファイル] [幅] [高さ] [開始時間] [終了時間] [フレーム数] - ビデオをGIFファイルに変換します

### 既知の問題
- !play [URL] - YouTubeの複数ビデオリストを再生できません
- !play [URL] - YouTubeのプレイリストを累積できません

### 1.5.ι (2023年12月22日)
![t2i](assets/preview/1.5.ι.png)
### 重要な変更
- 最初のパブリックリリースバージョン
- サーバーデータの保存方法を調整しました（データの保存先をserver/サーバーID/データサーバーID.jsonに変更）
- レベルシステムをリセットし、すべてのレベルを0に戻し、各レベルで必要な経験値を大幅に削減しました（以前は6レベル^4/2.5から6レベル^2/2.5に変更）

### 新機能
- !VoteCreate [質問] [選択肢1] [選択肢2] [選択肢N] - 投票を作成します
- !Vote [質問] [選択肢名] - 投票します
- !VoteResult [質問] - 投票結果を表示します
- !join - ボットをボイスチャットに参加させます
- !leave - ボットをボイスチャットから退出させます
- !play [URL] - 音楽を再生します（現在、StreetVoice、Youtubeの以下のプラットフォームをサポート）
- !GuessingGameStart - 数当てゲームを開始します
- !Guess [数字] - 数字を推測します
- !Tarot - タロットカードを引きます
- !PrimeNumber [整数] - 素数かどうかを判定します
- !Greeting [テキスト] - 独自の小規模AIモデルでテキストが挨拶かどうかを判断します（モデルバージョン: Project Hello Model 500）

### 既知の問題
- !play [URL] - YouTubeの複数ビデオリストを再生できません
- !play [URL] - YouTubeのプレイリストを累積できません

## クイックスタート
 **太字** の項目は必須です。
 
### ハードウェア要件
1. オペレーティングシステム：Windows
1. **CPU** / Nvidia GPU

### 環境設定
- **Python 3**
- ダウンロード: https://www.python.org/downloads/windows/
- **PyTorch**
- ダウンロード: https://pytorch.org/
- NVIDIA GPUドライバ
- ダウンロード: https://www.nvidia.com/zh-tw/geforce/drivers/
- NVIDIA CUDA Toolkit
- ダウンロード: https://developer.nvidia.com/cuda-toolkit
- NVIDIA cuDNN
- ダウンロード: https://developer.nvidia.com/cudnn
- **FFMPEG**
- ダウンロード: https://ffmpeg.org/download.html
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

