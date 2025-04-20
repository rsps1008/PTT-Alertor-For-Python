# PTT-Alertor-For-Python


PTT Alertor 是一個用於爬蟲 PTT 論壇特定板的新文章的 Python 程式。根據預先定義的條件，它可以通過 Line BOT 訊息服務向使用者發送通知。(僅測試python3版本)

## 運行方法

### 1. 安裝相依套件
在運行此腳本之前，需要安裝以下相依套件：
```bash
pip3 install requests beautifulsoup4
```

### 2. 取得 Line BOT Token
在 **<font color=orange>config.json</font>** 中的 `line_token: token` 變數中填入 Line BOT Token。<br>
```json
{ 
	"line_token":	[
						"填入你的Token",
						"7Ln/S...",
						"AcoQc...",
						"3rgw...",
						"7XdJG..."
					],
	"line_receiver": "Ud085...填入接收者訊息(請參考LINE_BOT)",
}
```
LINE BOT: https://github.com/rsps1008/LINE_BOT/

### 3. 雲端空間放置 Config 配置檔
放置 **<font color=orange>config.json</font>** 到公開的雲端空間中(例如: Google雲端硬碟，並設定權限為公開)，複製分享的網址並取代 **<font color=green>pttAlertor.py</font>** 變數: `file_url_GD` 之中的網址

### 4. 運行程式
在終端機中執行以下指令來運行腳本：
```bash
python3 pttAlertor.py
```

### 5. 等待通知
程式會定期檢查 PTT 版面並根據設定的條件發送 Line 通知。

## 配置設定

你可以修改 **<font color=orange>config.json</font>** 中的參數來設定想要監控的不同板以及相關條件(**關鍵字**、**推文數**與**作者**)。<br>以下是 **<font color=orange>config.json</font>** 的 Json 範例：

```python
keyword_dict = {
	"Lifeismoney":  { 
						"key":[["Line","pay"],["point"],["蝦皮"],["導購"]], 
						"push":50 
					}, 
	"Kaohsiung":    { 
						"author":["exelop"] 
					}
    # 其他通知觸發設定...
}
