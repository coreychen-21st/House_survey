import re
from playwright.sync_api import sync_playwright
from .base import BaseCrawler


class F591Crawler(BaseCrawler):
    source = "591"
    DETAIL_URL = "https://sale.591.com.tw/home/house/detail/2"

    def crawl(self):
        print("[591] 正在使用 Playwright 渲染爬取...")
        results = []
        base_url = "https://sale.591.com.tw/?shType=list&regionid=1&totalprice=300_1300&area=19_&room=2_&firstRow=0&totalRows=30"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                }
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
                        const results = [];
                        const allAnchors = document.querySelectorAll('a[href*="detail"]');
                        const seen = new Set();
                        allAnchors.forEach(a => {
                            const href = a.href;
                            if (seen.has(href)) return;
                            seen.add(href);
                            const parent = a.closest('li, div[class], section[class]') || a;
                            const text = (parent || a).innerText || '';
                            const img = (parent || a).querySelector('img');
                            const titleEl = (parent || a).querySelector('[class*="title"], h3, [class*="subject"]');
                            const priceEl = (parent || a).querySelector('[class*="price"]');
                            const addrEl = (parent || a).querySelector('[class*="address"], [class*="addr"]');
                            const areaEl = (parent || a).querySelector('[class*="area"], [class*="ping"], [class*="sqft"]');
                            results.push({
                                title: titleEl ? titleEl.innerText.trim() : '',
                                price: priceEl ? priceEl.innerText.trim() : text,
                                area: areaEl ? areaEl.innerText.trim() : text,
                                link: href,
                                image: img ? (img.src || img.getAttribute('data-src') || '') : '',
                                address: addrEl ? addrEl.innerText.trim() : text.split('\\n').slice(0,3).join(' ')
                            });
                        });
                        return results;
                    }""")

                    if not listings or len(listings) == 0:
                        break

                    for li in listings:
                        item = self._parse_js_item(li)
                        if item:
                            enriched = self.enrich_listing(item)
                            if self.basic_filter(enriched):
                                results.append(enriched)

                    print(f"[591] offset={offset}: {len(listings)} 筆")
                    offset += 30
                    self.sleep()

                except Exception as e:
                    print(f"[591] offset={offset} 錯誤: {e}")
                    break

            browser.close()

        print(f"[591] 總計 {len(results)} 筆")
        return results

    def _parse_js_item(self, obj):
        if not obj:
            return None

        title = obj.get("title", "")[:50]
        address = obj.get("address", "")[:80]
        raw_text = obj.get("price", "") + " " + obj.get("area", "")

        total_price = 0
        prices = re.findall(r"([\d,]+)\s*萬", str(raw_text))
        for p in prices:
            try:
                v = float(p.replace(",", ""))
                if 300 <= v <= 1300:
                    total_price = v
                    break
            except:
                pass
        if total_price == 0 and prices:
            for p in prices:
                try:
                    v = float(p.replace(",", ""))
                    if v >= 300:
                        total_price = v
                        break
                except:
                    pass

        area_ping = 0
        areas = re.findall(r"([\d.]+)\s*坪", str(raw_text))
        if areas:
            for a in areas:
                try:
                    v = float(a)
                    if 15 <= v <= 200:
                        area_ping = v
                        break
                except:
                    pass

        rooms = self.parse_rooms(str(raw_text))
        halls = self.parse_halls(str(raw_text))
        baths = self.parse_baths(str(raw_text))

        building_age = 0
        age_m = re.search(r"([\d.]+)\s*年", str(raw_text))
        if age_m:
            building_age = float(age_m.group(1))

        building_type = ""
        for bt in ["公寓", "大樓", "華廈", "透天", "別墅", "電梯"]:
            if bt in str(raw_text):
                building_type = bt
                break

        link = obj.get("link", "")
        house_id = ""
        m = re.search(r"detail/2/(\d+)", link)
        if m:
            house_id = m.group(1)

        img_url = obj.get("image", "")
        if img_url and not img_url.startswith("http"):
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            else:
                img_url = ""

        unit_price = 0
        up_m = re.search(r"([\d.]+)\s*萬\s*/\s*坪", str(raw_text))
        if up_m:
            unit_price = float(up_m.group(1))
        elif area_ping > 0 and total_price > 0:
            unit_price = round(total_price / area_ping, 2)

        return {
            "title": title, "address": address, "district": "",
            "total_price": total_price, "unit_price": unit_price,
            "area_ping": area_ping, "rooms": rooms, "halls": halls,
            "baths": baths, "building_age": building_age,
            "building_type": building_type, "floor": "",
            "image_urls": img_url, "floorplan_url": "",
            "url": link or f"{self.DETAIL_URL}/{house_id}.html",
            "description": "", "listed_date": "", "house_id": house_id,
        }
