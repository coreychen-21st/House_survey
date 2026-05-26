import sys
sys.path.insert(0, "D:\\House_survey")

from storage.database import init_db
init_db()
print("DB init OK")

from crawlers.yungching import YungChingCrawler
print("\n=== Testing YungChing ===")
yc = YungChingCrawler()
try:
    results = yc.crawl()
    print(f"Total results: {len(results)}")
    for r in results[:5]:
        print(f"  {r['total_price']} - {r.get('area_ping',0)} - {r.get('rooms',0)}R {r.get('title','')[:30]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

from crawlers.sinyi import SinyiCrawler
print("\n=== Testing Sinyi ===")
sy = SinyiCrawler()
try:
    results = sy.crawl()
    print(f"Total results: {len(results)}")
    for r in results[:5]:
        print(f"  {r['total_price']} - {r.get('area_ping',0)} - {r.get('rooms',0)}R {r.get('title','')[:30]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

from crawlers.f591 import F591Crawler
print("\n=== Testing 591 ===")
f5 = F591Crawler()
try:
    results = f5.crawl()
    print(f"Total results: {len(results)}")
    for r in results[:5]:
        print(f"  {r['total_price']} - {r.get('area_ping',0)} - {r.get('rooms',0)}R {r.get('title','')[:30]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
