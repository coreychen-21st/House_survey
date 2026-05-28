import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

PRICE_MIN = 300
PRICE_MAX = 1488

MIN_AREA_PING = 19
MIN_ROOMS = 2
MAX_BUILDING_AGE = 46

TARGET_CITY = "台北市"

NEGATIVE_KEYWORDS = [
    "凶宅", "非自然死亡", "刑事案件", "海砂屋", "鋼筋裸露",
    "壁癌", "輻射屋", "嚴重漏水", "傾斜", "土壤液化",
    "土石流", "爛建商", "頂樓加蓋", "頂加", "頂樓增建"
]

REQUEST_DELAY = 2
MAX_PAGES = 50

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "listings.db")
