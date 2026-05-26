import sys
sys.path.insert(0, "D:\\House_survey")

from storage.database import init_db
init_db()

print("TESTING YUNGCHING (1 page)")
from crawlers.yungching import YungChingCrawler
yc = YungChingCrawler()
yc.MAX_PAGES = 1

# Monkey-patch crawl to only 1 page
orig_crawl = yc.crawl
def one_page():
    results = []
    url = yc._build_url(1)
    items = yc._fetch_and_parse(url)
    if items:
        for item in items:
            enriched = yc.enrich_listing(item)
            if yc.basic_filter(enriched):
                results.append(enriched)
    print(f"  Results: {len(results)}")
    for r in results[:5]:
        print(f"  {r['total_price']} {r['area_ping']}p {r['rooms']}R/{r['halls']}H {r['building_age']}Y - {r['title'][:30]}")
    return results

one_page()

print("\nTESTING SINYI (1 page)")
from crawlers.sinyi import SinyiCrawler
sy = SinyiCrawler()
items = sy._fetch_and_parse()
if items:
    results = []
    for item in items:
        enriched = sy.enrich_listing(item)
        if sy.basic_filter(enriched):
            results.append(enriched)
    print(f"  Results: {len(results)}")
    for r in results[:5]:
        print(f"  {r['total_price']} {r['area_ping']}p {r['rooms']}R/{r['halls']}H {r['building_age']}Y - {r['title'][:30]}")
else:
    print("  No items")
