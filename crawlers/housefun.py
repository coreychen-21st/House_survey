import re
import httpx
from bs4 import BeautifulSoup

from .base import BaseCrawler
from config.settings import MAX_PAGES


class HousefunCrawler(BaseCrawler):
    source = "housefun"
    BASE_URL = "https://buy.housefun.com.tw"

    def crawl(self):
        results = []
        empty_streak = 0

        for page in range(1, MAX_PAGES + 1):
            url = self._build_url(page)
            print(f"[好房網] 爬取第 {page} 頁, url={url}")

            try:
                html = self._fetch(url)
                if not html:
                    empty_streak += 1
                    if empty_streak >= 3:
                        break
                    continue

                items = self._parse_page(html)
                if not items:
                    empty_streak += 1
                    if empty_streak >= 3:
                        break
                    continue

                empty_streak = 0
                added = 0
                for item in items:
                    enriched = self.enrich_listing(item)
                    if self.basic_filter(enriched):
                        results.append(enriched)
                        added += 1

                print(f"[好房網] 第 {page} 頁: {len(items)} 筆, 過濾後 +{added} 筆")
                self.sleep()

            except Exception as e:
                print(f"[好房網] 第 {page} 頁錯誤: {e}")
                break

        print(f"[好房網] 總計 {len(results)} 筆")
        return results

    def _build_url(self, page):
        if page == 1:
            return self.BASE_URL
        return f"{self.BASE_URL}/?pg={page}"

    def _fetch(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
        resp = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
        print(f"  HTTP {resp.status_code}, final_url={resp.url}")
        if resp.status_code != 200:
            return ""
        return resp.text

    def _parse_page(self, html):
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("section.m-list-obj")
        if not cards:
            cards = soup.select("section[class*='list-obj']")

        items = []
        for card in cards:
            item = self._parse_card(card)
            if item:
                items.append(item)
        return items

    def _parse_card(self, card):
        link_el = card.select_one(".casename > a[href^='/buy/house/']")
        if not link_el:
            link_el = card.select_one("a.m-list-figure[href^='/buy/house/']")
        if not link_el:
            return None

        href = link_el.get("href", "")
        url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        house_id = ""
        m = re.search(r"/buy/house/(\d+)", href)
        if m:
            house_id = m.group(1)
        if not house_id:
            return None

        title = link_el.get_text(strip=True)

        addr_el = card.select_one(".address-map address.address")
        address = addr_el.get_text(strip=True) if addr_el else ""

        area_ping = 0
        area_el = card.select_one(".ping-pattern .ping-number .number")
        if area_el:
            area_ping = self.parse_area(area_el.get_text(strip=True))

        pattern_el = card.select_one(".ping-pattern .pattern")
        pattern_text = pattern_el.get_text(" ", strip=True) if pattern_el else ""
        rooms = self.parse_rooms(pattern_text)
        halls = self.parse_halls(pattern_text)
        baths = self.parse_baths(pattern_text)

        floor_el = card.select_one(".ping-pattern .floor")
        floor = floor_el.get_text(strip=True) if floor_el else ""

        total_price = 0
        price_el = card.select_one(".price a.discount-price .number")
        if price_el:
            total_price = self.parse_price(price_el.get_text(strip=True))
        if total_price == 0:
            text = card.get_text(" ", strip=True)
            pm = re.search(r"(\d[\d,]*)\s*萬", text)
            if pm:
                total_price = self.parse_price(pm.group(1))

        unit_price = 0
        if area_ping > 0 and total_price > 0:
            unit_price = round(total_price / area_ping, 2)

        img_url = ""
        img = card.select_one(".m-list-figure-bd img")
        if img:
            img_url = img.get("data-src", "") or img.get("src", "")
            if img_url and img_url.startswith("//"):
                img_url = "https:" + img_url

        tags = []
        for t in card.select(".info .tag .tag-category"):
            txt = t.get_text(strip=True)
            if txt:
                tags.append(txt)

        return {
            "title": title,
            "address": address,
            "district": "",
            "total_price": total_price,
            "unit_price": unit_price,
            "area_ping": area_ping,
            "rooms": rooms,
            "halls": halls,
            "baths": baths,
            "building_age": 0,
            "building_type": "",
            "floor": floor,
            "image_urls": img_url,
            "floorplan_url": "",
            "url": url,
            "description": " ".join(tags)[:300],
            "listed_date": "",
            "house_id": house_id,
        }
