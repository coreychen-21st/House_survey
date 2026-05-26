import sys
sys.path.insert(0, "D:\\House_survey")
from crawlers.yungching import YungChingCrawler
from storage.database import init_db

init_db()
yc = YungChingCrawler()
url = yc._build_url(1)
items = yc._fetch_and_parse(url)

print(f"Total: {len(items)}")
in_range = [i for i in items if 300 <= i['total_price'] <= 1300]
print(f"In range 300-1300: {len(in_range)}")

for i, item in enumerate(items):
    in_r = "Y" if 300 <= item['total_price'] <= 1300 else "N"
    print(f"  [{in_r}] {item['total_price']}w {item['area_ping']}p {item['rooms']}R/{item['halls']}H {item['building_age']}y - {item['title'][:30]}")
