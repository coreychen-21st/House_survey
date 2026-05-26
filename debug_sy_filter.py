import sys
sys.path.insert(0, "D:\\House_survey")
from crawlers.sinyi import SinyiCrawler
from storage.database import init_db

init_db()
sy = SinyiCrawler()
items = sy._fetch_and_parse()
print(f"Total items: {len(items)}")
for i, item in enumerate(items[:20]):
    enriched = sy.enrich_listing(item)
    result = sy.basic_filter(enriched)
    print(f"[{'Y' if result else 'N'}] {item['total_price']:.0f}w {item['area_ping']:.1f}P {item['rooms']}R/{item['halls']}H {item['building_age']}Y {item['building_type']} - {item['title'][:20]}")
