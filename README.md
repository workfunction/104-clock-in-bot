# 104企業大師簽到機器人

這支程式針對 [104企業大師 私人秘書](https://pro.104.com.tw/psc2) 網站的使用者。

> **Warning**
>
> **!!! 重要 請先測試您的帳號登入流程 !!!**
>
> 本機器人沒有經過完整條件測試，請先用無痕視窗登入 [https://pro.104.com.tw/psc2](https://pro.104.com.tw/psc2)
>
> 確定您的帳號登入步驟為:
>
> 1. 輸入帳號密碼
> 2. 輸入email驗證碼
> 3. 打卡頁面
>
> 任何提醒更改密碼等帳號通知都會讓登入失敗!!

> **Warning**
>
> **!!! 重要 請先測試您的帳號登入流程 !!!**
>
> 目前只支援 macos!!

## 使用方式

1. 請先開啟 macos 同步 Microsoft Exchange 郵件
2. 安裝自動取得驗證碼的 [Shortcuts](https://www.icloud.com/shortcuts/87c4e347b8aa43bcbc50da582ebe4bbd)
3. 填入 `secret.sh`
4. 填入 `firebase-cred.json`
5. 執行 `setup.sh`
6. 執行 `source env-104-bot/bin/activate`
7. 執行 `run.sh`

WIP

### 帳號密碼登入

WIP

### 自動登入

WIP

### 定時執行

WIP

## 參數

WIP

## Exit Code

| Exit code | 解釋               |
| --------- | ------------------ |
| 0         | 簽到成功。         |
| 1         | 非上班日，跳過簽到 |
| 88        | 不明錯誤。         |
