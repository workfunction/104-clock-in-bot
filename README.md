# 104企業大師簽到機器人

這是針對 [104企業大師 私人秘書](https://pro.104.com.tw/psc2) 網站的自動簽到程式。

## 注意事項

**警告**

1. **!!! 重要 請先測試您的帳號登入流程 !!!**

   本機器人未經過完整測試，請先使用無痕視窗登入 [https://pro.104.com.tw/psc2](https://pro.104.com.tw/psc2)。

   確定您的帳號登入步驟如下：

   1. 輸入帳號密碼
   2. 輸入 email 驗證碼
   3. 打卡頁面

   任何更改密碼等帳號通知都可能導致登入失敗！！

2. **目前僅支援 macOS**

   請注意，目前此程式僅支援 macOS 系統，其他操作系統可能會遇到問題。

## 先前準備

在開始使用本程式之前，請確定完成以下步驟：

1. **開啟 macOS 同步 Microsoft Exchange 郵件**

    請先開啟 macOS 系統的郵件應用程式，確定已設定 Microsoft Exchange 郵件帳號並同步成功。在使用本程式的過程中，有可能會使用郵件驗證碼進行登錄。

2. **安裝自動取得驗證碼的 [Shortcuts](https://www.icloud.com/shortcuts/87c4e347b8aa43bcbc50da582ebe4bbd)**

    請使用提供的連結下載並安裝自動取得驗證碼的 Shortcuts。這個 Shortcuts 將協助自動取得郵件中的驗證碼，以方便程式進行登錄操作。

3. **準備 Python 開發環境**

    如果你尚未擁有 Python 開發環境，請執行以下指令來設定 Python 虛擬環境並安裝相關套件：

    ```bash
    python -m venv env-104-bot
    source env-104-bot/bin/activate
    pip install pycryptodome firebase_admin selenium
    ```

    這些指令將會自動設定一個名為 `env-104-bot` 的 Python 虛擬環境，並安裝必要的套件以便程式運行。

## 使用方式

你可以按照以下方式執行程式：

```bash
python main.py <username> <password> [-k <aes_key>] [-f <firebase_url>] [-t <teams_hook_url>] [-c]
```

在上述指令中，你需要提供你的 104 企業大師網站的帳號和密碼。以下是一些範例：

1. 使用最基本的參數執行：

   ```bash
   python main.py user@example.com password
   ```

2. 使用所有選擇性參數執行，並清除 cookies：

   ```bash
   python main.py user@example.com password -k a1ce16bcad88e60a2f802b35bac42017dde1c8f248f9970bd418989b33b8bdec -f https://your-project-default-rtdb.firebaseio.com -t https://example.webhook.office.com/webhookb2/foo/IncomingWebhook/bar -c
   ```

請注意，上述範例僅供參考。更詳細的參數說明，你可以參考 [參數說明](#參數說明) 章節。

## 參數說明

這個程式可以透過指令列接受以下參數：

- `<username>` (必要): 你的 104 帳號的電子郵件地址。
- `<password>` (必要): 你的 104 帳號的密碼。
- `-k`, `--aes_key` (選擇性): 用於加密和解密的 AES 金鑰。必須提供一個隨機的 64 位 16 進位(hex) 數，例如：`a1ce16bcad88e60a2f802b35bac42017dde1c8f248f9970bd418989b33b8bdec`。
- `-f`, `--firebase_url` (選擇性): 用於儲存 cookie 的 Firebase DB URL。如果沒有提供此參數，cookie 將會存到專案目錄下的 `cookie.json` 檔案中。
- `-t`, `--teams_hook_url` (選擇性): 用於發送通知的 MS Teams hook URL。如果沒有提供此參數，將會跳過 Teams 通知推送。
- `-c`, `--clear_cookies` (選擇性): 如果提供了此選項，將會清除 Firebase 上的 cookie 以及專案目錄下的 `cookie.json` 檔案。

這些參數可用於指定程式的執行方式和行為。注意：`<username>` 和 `<password>` 參數是必需的，而其他參數是選擇性的。

## 結束程式

程式執行完畢後會返回一個結束碼，可作為參考：

- `0`: 簽到成功。
- `1`: 非上班日，跳過簽到。
- `88`: 不明錯誤。

你可以根據結束碼判斷簽到操作的結果。

## 定時執行

為了定期執行簽到程式，你可以依照以下步驟：

1. **設定必要的參數**

   首先，建立一個名為 `secret.sh` 的檔案，並填入以下變數，替換其中的內容為你的帳號資訊和其他必要資料：

   ```
   # Your email address for 104 account
   USER="user@example.com"
   # Your password for 104 account
   PASS="password"
   # A random 64 digits hex numbers
   KEY="a1ce16bcad88e60a2f802b35bac42017dde1c8f248f9970bd418989b33b8bdec"
   # Your firebase access URL
   FIREBASE_URL="https://your-project-default-rtdb.firebaseio.com"
   # Your webhook API for teams notification
   TEAMS_URL="https://example.webhook.office.com/webhookb2/foo/IncomingWebhook/bar"
   ```

2. **設定 Firebase**

   前往 Firebase 網站建立一個新的專案。完成後，從 Firebase 專案設定中下載專案的 credential JSON 檔案並複製到專案最上層，並將其命名為 `firebase-cred.json`。

3. **執行程式**

   建立一個 `run.sh` 檔案，並填入以下指令，這將會設定 Python 虛擬環境、讀取 `secret.sh` 檔案中的變數，然後執行主程式：

   ```bash
   source /path/to/your/project/env-104-bot/bin/activate
   source /path/to/your/project/secret.sh
   python /path/to/your/project/main.py "$USER" "$PASS" -t "$TEAMS_URL" -k "$KEY" -f "$FIREBASE_URL"
   ```

   你可以根據需要修改路徑和選擇性參數。並嘗試執行 run.sh 來測試是否可以成功簽到。

4. **安裝定時任務**

   最後，執行以下指令來安裝定時任務，這將會使你的程式定期執行：

   ```bash
   if [ -f ~/Library/LaunchAgents/com.workfunction.104clockin.plist ]; then
      launchctl unload ~/Library/LaunchAgents/com.workfunction.104clockin.plist
   fi

   cp com.workfunction.104clockin.plist ~/Library/LaunchAgents/
   launchctl load -w ~/Library/LaunchAgents/com.workfunction.104clockin.plist
   ```

   這將會將專案提供的 plist 檔案安裝到系統中，讓系統於每日上午 8 點以及下午 5 點 30 分執行 `run.sh`。

   你可以在 `com.workfunction.104clockin.plist` 檔案中修改定時執行的時間。

   在這個 plist 檔案中，你可以找到以下段落：

   ```xml
   <key>StartCalendarInterval</key>
   <dict>
       <key>Hour</key>
       <integer>8</integer>
       <key>Minute</key>
       <integer>0</integer>
   </dict>
   <key>StartCalendarInterval</key>
   <dict>
       <key>Hour</key>
       <integer>17</integer>
       <key>Minute</key>
       <integer>30</integer>
   </dict>
   ```

   你可以修改 `<integer>` 元素的值來設定定時執行的小時和分鐘。例如，如果你想要改成上午 9 點和下午 6 點執行，可以將其修改為：

   ```xml
   <key>StartCalendarInterval</key>
   <dict>
       <key>Hour</key>
       <integer>9</integer>
       <key>Minute</key>
       <integer>0</integer>
   </dict>
   <key>StartCalendarInterval</key>
   <dict>
       <key>Hour</key>
       <integer>18</integer>
       <key>Minute</key>
       <integer>0</integer>
   </dict>
   ```

   修改完畢後，儲存文件並使用上述指令重新安裝至系統，系統便會在指定的時間執行 `run.sh` 檔案。
