import re
from .base import BaseCrawler


class F591Crawler(BaseCrawler):
    source = "591"
    DETAIL_URL = "https://sale.591.com.tw/home/house/detail/2"

    def crawl(self):
        print("[591] 正在使用 Playwright 渲染爬取...")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[591] Playwright 未安裝，跳過")
            return []

        results = []
        base_url = "https://sale.591.com.tw/?shType=list&regionid=1&totalprice=300_1300&area=19_&room=2_&firstRow=0&totalRows=30"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            offset = 0
            while offset < 1500:
                url = base_url.replace("firstRow=0", f"firstRow={offset}")
                print(f"[591] offset={offset}")

                try:
                    page.goto(url, timeout=30000, wait_until="networkidle")
                    page.wait_for_timeout(3000)

                    listings = page.evaluate("""() => {
                        const items = [];
                        document.querySelectorAll('[class*="house-item"], [class*="houseItem"], [class*="list-item"], [class*="listItem"], .item, [class*="vue"]').forEach(el => {
                            const data = {
                                title: el.querySelector('[class*="title"], h3, .title')?.innerText || '',
                                address: el.querySelector('[class*="address"], [class*="addr"], .address')?.innerText || '',
                                price: el.querySelector('[class*="price"], .price')?.innerText || '',
                                area: el.querySelector('[class*="area"], .area')?.innerText || '',
                                rooms: el.querySelector('[class*="room"], .room')?.innerText || '',
                                link: el.querySelector('a[href*="detail"]')?.href || '',
                                image: el.querySelector('img')?.src || '',
                            };
                            if (data.price) items.push(data);
                        });
                        return items;
                    }""")

                    if not listings:
                        content = page.content()
                        items = self._parse_html(content)
                    else:
                        items = []
                        for li in listings:
                            item = self._parse_js_item(li)
                            if item:
                                items.append(item)

                    if not items:
                        break

                    for item in items:
                        enriched = self.enrich_listing(item)
                        if self.basic_filter(enriched):
                            results.append(enriched)

                    print(f"[591] offset={offset}: {len(items)} 筆")
                    offset += 30
                    self.sleep()

                except Exception as e:
                    print(f"[591] offset={offset} 錯誤: {e}")
                    break

            browser.close()

        print(f"[591] 總計 {len(results)} 筆")
        return results

    def _parse_js_item(self, obj):
        if not obj or not obj.get("price"):
            return None

        title = obj.get("title", "")
        address = obj.get("address", "")

        price_text = obj.get("price", "0")
        total_price = self.parse_price(price_text)

        area_text = obj.get("area", "0")
        area_ping = self.parse_area(area_text)

        rooms = self.parse_rooms(obj.get("rooms", ""))
        halls = self.parse_halls(obj.get("rooms", ""))
        baths = self.parse_baths(obj.get("rooms", ""))

        link = obj.get("link", "")
        house_id = ""
        m = re.search(r"detail/(?:2/)?(\d+)", link)
        if m:
            house_id = m.group(1)

        img_url = obj.get("image", "")

        unit_price = 0
        if area_ping > 0 and total_price > 0:
            unit_price = round(total_price / area_ping, 2)

        return {
            "title": title, "address": address, "district": "",
            "total_price": total_price, "unit_price": unit_price,
            "area_ping": area_ping, "rooms": rooms, "halls": halls,
            "baths": baths, "building_age": 0, "building_type": "",
            "floor": "", "image_urls": img_url, "floorplan_url": "",
            "url": link or f"{self.DETAIL_URL}/{house_id}.html",
            "description": "", "listed_date": "", "house_id": house_id,
        }

    def _parse_html(self, html):
        items = []
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        for item_el in soup.select("[class*='house-item'], [class*='list-item'], .item"):
            title_el = item_el.select_one("[class*='title'], .title, h3")
            price_el = item_el.select_one("[class*='price'], .price")
            addr_el = item_el.select_one("[class*='address'], .address")
            area_el = item_el.select_one("[class*='area'], .area")
            img_el = item_el.select_one("img")
            link_el = item_el.select_one("a[href*='detail']")

            title = title_el.get_text(strip=True) if title_el else ""
            price_text = price_el.get_text(strip=True) if price_el else ""
            address = addr_el.get_text(strip=True) if addr_el else ""
            area_text = area_el.get_text(strip=True) if area_el else ""

            total_price = self.parse_price(price_text)
            area_ping = self.parse_area(area_text)
            img_url = img_el.get("src", "") if img_el else ""
            link = link_el.get("href", "") if link_el else ""
            house_id = re.search(r"detail/(?:2/)?(\d+)", link).group(1) if link else ""

            if not title and not price_text:
                continue

            items.append({
                "title": title, "address": address, "district": "",
                "total_price": total_price, "unit_price": 0,
                "area_ping": area_ping, "rooms": 0, "halls": 0,
                "baths": 0, "building_age": 0, "building_type": "",
                "floor": "", "image_urls": img_url, "floorplan_url": "",
                "url": link or f"{self.DETAIL_URL}/{house_id}.html",
                "description": "", "listed_date": "", "house_id": house_id,
            })

        return items
