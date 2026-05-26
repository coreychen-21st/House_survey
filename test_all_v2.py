import sys
sys.path.insert(0, "D:\\House_survey")
from storage.database import init_db
init_db()

print("=" * 50)
print("TESTING YUNGCHING (3 pages)")
print("=" * 50)
from crawlers.yungching import YungChingCrawler
yc = YungChingCrawler()
results_yc = yc.crawl()
print(f"  TOTAL: {len(results_yc)}")

print("\n" + "=" * 50)
print("TESTING SINYI")
print("=" * 50)
from crawlers.sinyi import SinyiCrawler
sy = SinyiCrawler()
results_sy = sy.crawl()
print(f"  TOTAL: {len(results_sy)}")

print("\n" + "=" * 50)
print("TESTING 591 (Playwright)")
print("=" * 50)
from crawlers.f591 import F591Crawler
f5 = F591Crawler()
results_591 = f5.crawl()
print(f"  TOTAL: {len(results_591)}")

print("\n" + "=" * 50)
print(f"GRAND TOTAL: {len(results_yc) + len(results_sy) + len(results_591)}")
print("=" * 50)

# Show samples
all_results = results_yc + results_sy + results_591
all_results.sort(key=lambda x: x["total_price"])
for r in all_results[:15]:
    print(f"  [{r['source']:10s}] {r['total_price']:>8.0f}万 {r['area_ping']:>6.1f}P {r['rooms']}R/{r['halls']}H/{r['baths']}B {r['building_age']:>5.0f}Y - {r['title'][:25]}")
