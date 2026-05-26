# House Survey

定期爬取信義房屋、永慶房屋、591 三大房仲平台，
篩選台北市 300萬-1300萬、2房以上、屋齡46年以下物件，
排除凶宅、海砂屋、壁癌等問題屋，跨站去重後推送 Telegram。

## 設定

1. 在 GitHub Actions Secrets 中設定：
   - `TELEGRAM_BOT_TOKEN`：Telegram Bot Token
   - `TELEGRAM_CHAT_ID`：目標 Chat ID

2. GitHub Actions 每 6 小時自動執行

## 條件

- 台北市
- 價格: 300 萬 - 1300 萬
- 坪數 >= 19 坪
- 格局 >= 2 房
- 屋齡 < 46 年
- 排除: 凶宅、海砂屋、鋼筋裸露、壁癌、傾斜、土壤液化、土石流等

## 本地執行

```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```
# House_survey
# House_survey
# House_survey
# House_survey
# House_survey
# House_survey
# House_survey
# House_survey
# House_survey
