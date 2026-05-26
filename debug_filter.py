import sys
sys.path.insert(0, "D:\\House_survey")
from crawlers.yungching import YungChingCrawler
from storage.database import init_db

init_db()
yc = YungChingCrawler()
url = yc._build_url(1)
items = yc._fetch_and_parse(url)

print(f"Total parsed items: {len(items)}")
for i, item in enumerate(items[:5]):
    print(f"\nItem {i}:")
    for k, v in item.items():
        print(f"  {k}: {v}")

# Now test filter
print("\n\n=== FILTER TEST ===")
for i, item in enumerate(items[:5]):
    enriched = yc.enrich_listing(item)
    result = yc.basic_filter(enriched)
    print(f"Item {i}: filter={result}")
    print(f"  price={item['total_price']}, area={item['area_ping']}, rooms={item['rooms']}, age={item['building_age']}")
    print(f"  price in range: {300 <= item['total_price'] <= 1300}")
    print(f"  area >= 19: {item['area_ping'] >= 19}")
    print(f"  rooms >= 2: {item['rooms'] >= 2}")
    print(f"  age <= 46: {item['building_age'] <= 46}")
