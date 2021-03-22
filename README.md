## Fugle API 繪製分K行情圖範例

本專案使用玉山 Fugle API 作為資料來源，與Telegram/LINE Bot結合，利用Flask做callback server，實現報價及分K行情圖繪製

目前已實現的功能: 
- 個股分K圖 (含5MA+30MA)
- 個股日K圖 (BBANDS + 5MA + 60MA)
- 最佳五檔

---

### 安裝前須知

- 需在玉山 Fugle 開戶並申請 API Token，詳細 API 請求方式請參考[官方文件](https://developer.fugle.tw/document/intraday/introduction)

- Telegram Bot Token 申請

---

### 安裝依賴套件

`pip install -r requirements.txt`

註: 其中Ta-lib為非官方套件，需[手動安裝](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)

下載對應的python 版本及 32/64位元的whl檔後，切換至該目錄執行以下指令安裝

`pip install file_name.whl`

---
### 更新 config 檔

複製一份專案根目錄下 `config.ini.example` 檔，並改名為 `config.ini` ，依照註解填入對應的值
```ini
[TELEGRAM]
; TG Bot 的 Token
ACCESS_TOKEN =

[LINE]
; LINE Bot 的 API Token及 Secret
LINE_BOT_API =
LINE_BOT_SECRET =

[SERVER]
; 此專案要準備可供 Line Bot / TG Bot callback用的位址 (需要有https，若無對外連線的配置可以用ngrok)
SERVER_URL = 

[FUGLE]
; 玉山 fugle 的 API domain 及 API Token
API_URL =
TOKEN =

[HOST]
; flask 啟動時的Host 及 Port
HOST =
PORT =
```

啟動 flask server
```ini
activate {env_name} && python main.py
```
-----
## Debug方式:
可將HOST填入`127.0.0.1` 並使用 `getStockGraph` API作為測試

method: GET

parameters:

var| required|description
----|:----:|:-----
stock_id|*|股票代號
plot_type| |填入m代表畫日K圖
