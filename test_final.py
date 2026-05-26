import sys
sys.path.insert(0, "D:\\House_survey")
from storage.database import init_db
init_db()

TEST_SOURCES = ["yungching", "sinyi", "houseprice"]

print("=" * 60)
print("FINAL INTEGRATION TEST")
print("=" * 60)

all_results = []

# YungChing
print("\n[1] YungChing")
from crawlers.yungching import YungChingCrawler
yc = YungChingCrawler()
results = yc.crawl()
all_results.extend(results)

# Sinyi
print("\n[2] Sinyi")
from crawlers.sinyi import SinyiCrawler
sy = SinyiCrawler()
results = sy.crawl()
all_results.extend(results)

# HousePrice
print("\n[3] 5168")
from crawlers.houseprice import HousePriceCrawler
hp = HousePriceCrawler()
results = hp.crawl()
all_results.extend(results)

# 591 (Playwright - skip if unavailable)
print("\n[4] 591")
from crawlers.f591 import F591Crawler
f5 = F591Crawler()
results = f5.crawl()
all_results.extend(results)

print("\n" + "=" * 60)
print(f"GRAND TOTAL: {len(all_results)} items")
print("=" * 60)

all_results.sort(key=lambda x: x["total_price"])
for r in all_results[:30]:
    print(f"  [{r['source']:12s}] {r['total_price']:>8.0f}w {r['area_ping']:>6.1f}P {r['rooms']}R/{r['halls']}H {r['building_age']:>5.0f}Y {r['building_type'][:6]:6s} - {r['title'][:30]}")

print(f"\nBy source:")
for src in TEST_SOURCES:
    count = sum(1 for r in all_results if r['source'] == src)
    print(f"  {src}: {count}")
