# ptt_alertor

PTT Alertor 是一個用於監控 PTT 論壇特定版面的新貼文的 Python 程式。根據預先定義的條件，它可以通過 Line 訊息服務向使用者發送通知。

## 運行方法

### 1. 安裝相依套件
    在運行此腳本之前，需要安裝以下相依套件：
    ```bash
    pip install requests beautifulsoup4
    ```

### 2. 設定 Line Notify Token
    在程式碼中的 `token` 變數中填入 Line Notify Token。

### 3. 配置檔案
    修改 `keyword_dict` 變數來設定要監控的 PTT 版面和相關條件。您可以設定關鍵字、推文數閾值、以及作者等。

### 4. 運行程式
    在終端機中執行以下指令來運行腳本：
    ```bash
    python pttAlertor.py
    ```

### 5. 等待通知
    程式會定期檢查 PTT 版面並根據設定的條件發送 Line 通知。

## 配置設定
您可以修改 `keyword_dict` 變數來設定您要監控的不同版面以及相關條件。以下是 `keyword_dict` 的範例：

```python
keyword_dict = {
    "Lifeismoney": {
        "key": [["Line", "pay"], ["pchome"], ["point"], ["蝦皮"]],
        "push": 50
    },
    "stock": {
        "author": ["a26893997", "blueian", "chengwaye", "robertshih", "nuggets", "newconfidenc", "guilty13", "drgon", "s10330076", "tamama000", "test520", "zesonpso"],
        "push": 90
    },
    # 其他版面設定...
}