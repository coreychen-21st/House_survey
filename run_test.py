import sys
sys.path.insert(0, "D:\\House_survey")

from storage.database import init_db
init_db()

# Test YungChing
print("\n" + "=" * 50)
print("TESTING YUNGCHING")
print("=" * 50)
from crawlers.yungching import YungChingCrawler
yc = YungChingCrawler()
try:
    results = yc.crawl()
    print(f"\nYungChing TOTAL: {len(results)}")
    for r in results[:10]:
        print(f"  {r['total_price']}万 {r['area_ping']}P {r['rooms']}R/{r['halls']}H {r['building_age']}Y {r['building_type']}")
        print(f"    addr={r['address'][:40]}, title={r['title'][:40]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test Sinyi
print("\n" + "=" * 50)
print("TESTING SINYI")
print("=" * 50)
from crawlers.sinyi import SinyiCrawler
sy = SinyiCrawler()
try:
    results = sy.crawl()
    print(f"\nSinyi TOTAL: {len(results)}")
    for r in results[:10]:
        print(f"  {r['total_price']}万 {r['area_ping']}P {r['rooms']}R/{r['halls']}H {r['building_age']}Y {r['building_type']}")
        print(f"    addr={r['address'][:40]}, title={r['title'][:40]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 591
print("\n" + "=" * 50)
print("TESTING 591")
print("=" * 50)
from crawlers.f591 import F591Crawler
f5 = F591Crawler()
try:
    results = f5.crawl()
    print(f"\n591 TOTAL: {len(results)}")
    for r in results[:10]:
        print(f"  {r['total_price']}万 {r['area_ping']}P {r['rooms']}R/{r['halls']}H {r['building_age']}Y {r['building_type']}")
        print(f"    addr={r['address'][:40]}, title={r['title'][:40]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
