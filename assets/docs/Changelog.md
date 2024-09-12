# Nagato-Sakura-Discord-Bot-py 所有發行版本
### 2.0.0 (2024 年 6 月 11 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/2.0.0.jpg)
### 重要變更
- 【重大】實裝「聊天」功能。
- 【重大】移除 models 資料夾，合併至 data 個別的資料夾。
- 【重大】cogs 只放置最基本的功能，需要其他功能需要用戶自己從 beta 及 extension 移動至 cogs 來啟用功能。
- 【移除】模型檔案，現在模型需要另外下載，減少倉庫空間提升 git clone 速度。
### 新增功能
- 【新增】!Chat - 和長門櫻聊天。
- 【新增】!Chat 附上錄音 - 和長門櫻聊天。
- 【新增】!ChatClear - 清除和長門櫻聊天記憶。
- 【新增】requirements.txt - 可以快速下載所運行需要的套件。
- 【更新】SuperDeformed - 新增了/指令，並且更改了送出的圖片。
- 【更新】GenerateBarCode - 新增了/指令。
### 已知問題
- 【錯誤】Youtube.py 使用/play [網址] 指令時，如果是播放清單會高機率報錯 (處理超時) ，建議使用播放清單時使用 !Play [網址] 來避免程式超時導致的報錯。

## 1.5.0 (2024 年 3 月 1 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.5.0.jpg)
### 重要變更
- 【重大】儲存庫文件整理，將部分說明文件移至assets/docs中。
- 【重大】資產調整，將原本的 png 改為 jpg 大幅減少了儲存庫容量並且提升了部分程式在 discord 的回應速度。
- 【重大】Del.py 移動至 beta - 刪除權限過大個人認為不適合在一般模式使用他，避免惡意使用。
- 【整合】Game.py 整合了 GuessingGame.py 及 SnakeGame.py 以後遊戲相關的功能將全部整合在這裡。
- 【整合】Image.py 整合了 Image.py 及 SuperDeformed.py 以後圖像相關的功能將全部整合在這裡。
- 【整合】Math.py 整合了 Math.py 及 PrimeNumber.py 以後計算相關的功能將全部整合在這裡。
- 【移除】!Userinfo [用戶名稱] - 由於與 !Level 功能過於類似故將其移除。
- 【移除】!Greeting [文字] - 該程式為 AutoReply.py 判斷的前身，他已經完美完成了他的任務是時候讓他走了。
### 新增功能
- 【更新】Del.py、Dice.py、Help.py、Ping.py、Vote.py 及 Youtube.py新增了/指令。
- 【更新】Version.py - 更新為符合新版資產的輸出格式。
- 【更新】Help.py - 刪除了按鈕並且重新改寫了鑲入內容。
- 【更新】FestivalEvent.py - 新增更多彩蛋內容。
- 【更新】CheckSMS.py - 現在能判斷出驗證碼簡訊後將驗證碼輸出，並且更新的模型版本。 [詳見分支專案](https://github.com/AmanoShizukikun/Nagato-Sakura-SMS-Checker/blob/main/assets/docs/Changelog.md#1042024-%E5%B9%B4-3-%E6%9C%88-1-%E6%97%A5)
- 【修復】CheckSMS.py - 修復了將有小數點的訊息誤認成網址的錯誤。
### 已知問題
- 【錯誤】Youtube.py 使用/play [網址] 指令時，如果是播放清單會高機率報錯 (處理超時) ，建議使用播放清單時使用 !Play [網址] 來避免程式超時導致的報錯。

## 1.4.1 (2024 年 2 月 26 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.4.1.jpg)
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

## 1.4.0 (2024 年 2 月 17 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.4.0.jpg)
### 重要變更
- 【重大】main_beta.py 新增了 載入指令程式檔案、卸載指令檔案、重新載入程式檔案、載入斜線指令。
- 【調整】大幅精簡了部分程式的行數，並且提高了程式的效率。
### 新增功能
- 【新增】!FestivalEvent - 特殊節日彩蛋。
- 【更新】DM.py 及 Tarot.py 新增了/指令。
### 已知問題
- 【錯誤】!Tarot - 無法產生正確圖片及正逆為牌意。

## 1.3.1 (2024 年 1 月 30 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.3.1.jpg)
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
  
## 1.3.0 (2024 年 1 月 9 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.3.0.jpg)
### 重要變更
- 【重大】刪除了 Music.py 改為 Youtube.py。(移除了對streetvoice支持)
### 新增功能
- 【新增】!List - 長門櫻顯示撥放清單。
- 【新增】!Skip [數字] - 跳過 [數字] 首歌。
- 【修復】!Help - 解決了幫助訊息過長無法傳出的問題。
- 【修復】修復了 Youtube 複數影片清單無法播放及 Youtube 無法累加播放清單的問題。
### 已知問題
- N/A 

## 1.2.0 (2024 年 1 月 3 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.2.0.jpg)
### 重要變更
- 【重大】調整伺服器資料的儲存方式。(AI模型該為從models資料夾讀取而非根目錄，並且新增beta分類。)
- 【重大】統一了所有 cogs 的格式。
- 【重大】TAG 長門櫻 並且附加檔案上去後，長門櫻會自動把檔案下載到運行伺服器上。
### 新增功能
- 【新增】!CheckSMS [文字] - 自製小型AI模型判斷簡訊類別。
- 【新增】!GenerateBarCode [12位數字] - 生成EAN13條碼。
- 【新增】!GenerateQRCode [內容] [數字] - 生成QRCode，數字決定QRCode造型可有可無。
- 【新增】!GenerateQRCode [內容] [數字] [附加圖片] - 生成崁入圖片的QRCode。
- 【新增】!Greeting [文字] - 自製小型AI模型判斷文字是否為打招呼
- 【新增】!PingIP [網址] - 查詢網站 IP。
- 【新增】!VideoToGif [附加影片檔] [寬] [高] [起始時間] [結束時間] [幀數] - 將影片生成Gif檔。
- 【新增】!Version - 顯示當前機器人版本。
- 【修復】!play [網址] - Youtube 單個影片播放修復完成
### 已知問題
- 【錯誤】!play [網址] - Youtube 複數影片播放錯誤。
- 【錯誤】!Help - 幫助訊息過長無法傳出。

## 1.1.0 (2023 年 10 月 1 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.1.0.jpg)
### 重要變更
- 【重大】調整伺服器資料的儲存方式 (存放方式改為將資料存到server/伺服器ID/資料伺服器ID.json)
- 【重大】重製等級系統，所有等級歸0，大幅降低每等所需經驗值 (原本6等級^4/2.5改為6等級^2/2.5)
- 【重大】CustomCommands.py 更改為無法在私人訊息觸發 (影響範圍: !Add、!Edit、!Remove)
### 新增功能
- 【新增】!GuessingGameStart - 開啟猜數字遊戲
- 【新增】!Guess [數字] - 猜數字
- 【新增】!Join - 長門櫻進入語音聊天室
- 【新增】!Leave - 長門櫻離開語音聊天室 
- 【新增】!Play [網址] - 長門櫻可以播放音樂(支援以下平台:StreetVoice)
- 【新增】!PrimeNumber [整數] - 判斷是否為質數
- 【新增】!Tarot - 抽塔羅牌
- 【新增】!VoteCreate [問題] [選項1] [選項2] [選項N] - 創建投票
- 【新增】!Vote [問題] [選項名稱] - 投票
- 【新增】!VoteResult [問題] - 顯示投票結果
- 【新增】!WebCrawler [網址] [輸出類別] - 爬蟲回傳輸出類別
### 已知問題
- 【錯誤】!Play [網址] - Youtube 無法播放 

## 1.0.0 (2023 年 9 月 16 日)
![t2i](https://github.com/AmanoShizukikun/Nagato-Sakura-Discord-Bot-py/blob/main/assets/preview/1.0.0.jpg)
### 重要變更
- 【重大】底層程式碼從NODE.js更改為Python。
### 新增功能
- 【新增】!Choices [選擇次數] [選項0] [選項1] ... - 隨機抽取選擇次數的選項(不重複)
- 【新增】!Del [數字] - 刪除[數字]條指令 (不包含私人聊天室)
- 【新增】!Dice [骰子面數] [擲骰次數] - 擲骰子
- 【新增】!DM - 邀請長門櫻私訊
- 【新增】!Help - 顯示幫助信息
- 【新增】!Level - 顯示個人資料卡
- 【新增】!MathHelp - 顯示計算指令
- 【新增】!Math - 長門櫻幫您計算數學
- 【新增】!Ping - 長門櫻在 Discord WebSocket 協議的延遲
- 【新增】!Translate [翻譯內容] - 自動中翻英，英翻中
- 【新增】!TranslateTo [語系] [翻譯內容] - 將翻譯內容翻譯成所選語系
- 【新增】!TranslateHelp - 顯示可翻譯語系
- 【新增】!Userinfo [用戶名稱] - 顯示詳細用戶資訊
- 【新增】!AllWeather - 顯示所有天氣
- 【新增】!Weather - 顯示六都天氣
- 【新增】!Weather [縣市名稱] - 顯示指定縣市天氣
### 已知問題
- N/A 
