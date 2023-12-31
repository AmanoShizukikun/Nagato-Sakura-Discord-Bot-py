# Discord-Bot-Nagato-Sakura-py

TIM_嚮導小妖精 Discord.py 版本

## 近期變動
### 1.5.ι (2023 年 12 月 22 日)
- 更新 !Greeting [文字] - 模型版本升級 : Project Hello Model 500
- 更新 !Help - 幫助信息添加新指令提示

### 1.5.θ (2023 年 12 月 21 日)
- 重要 調整伺服器資料的儲存方式 (AI模型該為從models資料夾讀取而非根目錄)
- 重要 模型優化調整，新增CUDA模式，提高模型效率
- 新增 !Greeting [文字] - 自製小型AI模型判斷文字是否為打招呼 (模型版本 : Project Hello Model 300)

### 1.5.η (2023 年 10 月 22 日)
- 修復 !play [網址] - Youtube 單個影片播放修復完成
- 故障 !play [網址] - Youtube 複數影片清單無法播放
- 故障 !play [網址] - Youtube 無法累加播放清單

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
- 下載: https://ffmpeg.zeranoe.com/builds/
```shell
python3 -m pip install -U discord.py
python3 -m pip install -U discord.py[voice]
pip install numpy
pip install numexpr
pip install googletrans==3.1.0a0
pip install requests
pip install openai
pip install youtube_dl
```
### 環境變數
- C:\Program Files\ffmpeg-master-latest-win64-gpl\bin

### youtube_dl修復
1. 尋找youtube-dl中的youtube.py
```shell
"C:\Users\使用者名稱\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\youtube_dl\extractor\youtube.py"
```
1. 修改youtube.py
修改第1794行 :
```shell
'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
直接註釋
```shell
#'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
```
1. 儲存youtube.py
