import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.database import init_db, get_new_listings, mark_notified
from dedup.matcher import process_and_store
from crawlers.yungching import YungChingCrawler
from crawlers.sinyi import SinyiCrawler
from crawlers.f591 import F591Crawler
from crawlers.houseprice import HousePriceCrawler
from notifier.telegram import notify_batch


def run_sync_crawlers():
    all_listings = []
    for name, crawler_cls in [
        ("永慶房屋", YungChingCrawler),
        ("信義房屋", SinyiCrawler),
        ("5168實價登錄比價王", HousePriceCrawler),
        ("591", F591Crawler),
    ]:
        try:
            print(f"\n[{name}] 開始...")
            crawler = crawler_cls()
            items = crawler.crawl()
            all_listings.extend(items)
            print(f"[{name}] 完成: {len(items)} 筆")
        except Exception as e:
            print(f"[{name}] 失敗: {e}")
    return all_listings


async def main():
    init_db()
    print("=" * 50)
    print("House Survey - 開始爬取房源")
    print("=" * 50)

    all_listings = run_sync_crawlers()

    print(f"\n合計爬取 {len(all_listings)} 筆原始物件")

    stored_ids = process_and_store(all_listings)
    print(f"存入 {len(stored_ids)} 筆新物件")

    new_listings = get_new_listings()
    print(f"待通知物件: {len(new_listings)} 筆")

    if new_listings:
        await notify_batch(new_listings)
        for item in new_listings:
            mark_notified(item["id"])

    print("\n完成!")


if __name__ == "__main__":
    asyncio.run(main())
