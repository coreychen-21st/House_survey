import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from .base import BaseCrawler
from config.settings import MAX_PAGES, PRICE_MIN, PRICE_MAX


class YungChingCrawler(BaseCrawler):
    source = "yungching"
    BASE_URL = "https://buy.yungching.com.tw"

    def crawl(self):
        print("[永慶] 正在使用 Playwright 渲染爬取...")
        results = []
        empty_streak = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                }
            )
            page = context.new_page()

            for pg in range(1, MAX_PAGES + 1):
                url = self._build_url(pg)
                print(f"[永慶] 爬取第 {pg} 頁, url={url}")

                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)

                    html = page.content()
                    if self.is_blocked_page(html, page.title()):
                        print("  偵測到 403/CloudFront 封鎖，快速停止")
                        break
                    print(f"  HTML length={len(html)}, 含 'house/' = {html.count('house/')}")

                    soup = BeautifulSoup(html, "lxml")
                    cards = self._find_cards(soup)
                    if not cards:
                        print(f"  未找到卡片，結束")
                        break

                    filter_count = 0
                    for card in cards:
                        href = card.get("href", "")
                        m = re.search(r"house/(\w+)", href)
                        if not m:
                            continue
                        house_id = m.group(1)
                        item = self._parse_card(card, house_id)
                        if item:
                            enriched = self.enrich_listing(item)
                            ok, reason = self.basic_filter_debug(enriched)
                            if ok:
                                results.append(enriched)
                                filter_count += 1
                            elif pg <= 3:
                                print(f"  過濾: {item.get('title','')[:30]} | price={item.get('total_price')} area={item.get('area_ping')} rooms={item.get('rooms')} age={item.get('building_age')} reason={reason}")

                    print(f"[永慶] 第 {pg} 頁: {len(cards)} 卡片, 過濾後 {filter_count} 筆")

                    if filter_count == 0:
                        empty_streak += 1
                    else:
                        empty_streak = 0

                    if empty_streak >= 3:
                        print(f"  連續 {empty_streak} 頁無符合物件，停止")
                        break

                    self.sleep()

                except Exception as e:
                    print(f"[永慶] 第 {pg} 頁錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    break

            browser.close()

        print(f"[永慶] 總計 {len(results)} 筆")
        return results

    def _build_url(self, page):
        base = f"{self.BASE_URL}/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_{PRICE_MIN}_{PRICE_MAX}/age_0_46/area_19_/room_2_"
        if page == 1:
            return base
        return base + f"?pg={page}"

    def _find_cards(self, soup):
        selectors_to_try = [
            "a.link[href*='house/']",
            "a[href*='house/']",
            "[class*='case-item']",
            "[class*='card']",
            "[class*='listing']",
            "li[class*='item']",
        ]
        for sel in selectors_to_try:
            cards = soup.select(sel)
            if cards:
                print(f"  選擇器 '{sel}' 找到 {len(cards)} 個卡片")
                return cards

        cards = soup.find_all("a", href=re.compile(r"house/\d+"))
        if cards:
            print(f"  正則 fallback 找到 {len(cards)} 個卡片")
            return cards

        snippet = str(soup)[:3000].replace("\n", " ")
        print(f"  HTML snippet: {snippet[:800]}...")
        return []

    def _parse_card(self, card, house_id):
        title = ""
        img = card.select_one("img")
        if img:
            title = img.get("alt", "") or img.get("title", "")

        if not title:
            case_name = card.select_one(".caseName")
            if case_name:
                title = case_name.get_text(strip=True)

        if not title:
            for t in ["h3", ".title", "[class*='title']", "[class*='name']"]:
                el = card.select_one(t)
                if el:
                    title = el.get_text(strip=True)
                    break

        address = ""
        addr_el = card.select_one(".address")
        if addr_el:
            address = addr_el.get_text(strip=True)

        case_info = card.select_one(".case-info")
        case_text = case_info.get_text(" ", strip=True) if case_info else ""

        building_type = ""
        type_el = card.select_one(".caseType")
        if type_el:
            building_type = type_el.get_text(strip=True)

        building_age = 0
        age_m = re.search(r"([\d.]+)\s*年", case_text)
        if age_m:
            building_age = float(age_m.group(1))

        area_ping = 0
        reg_area = card.select_one(".regArea")
        if reg_area:
            area_val = reg_area.get_text(strip=True)
            area_m = re.search(r"([\d.]+)", area_val)
            if area_m:
                area_ping = float(area_m.group(1))

        floor = ""
        floor_el = card.select_one(".floor")
        if floor_el:
            floor = floor_el.get_text(strip=True)

        room_text = ""
        room_el = card.select_one(".room")
        if room_el:
            room_text = room_el.get_text(strip=True)
        rooms = self.parse_rooms(room_text)
        halls = self.parse_halls(room_text)
        baths = self.parse_baths(room_text)

        description = ""
        note_el = card.select_one(".note")
        if note_el:
            description = note_el.get_text(strip=True)

        if not description:
            tag_els = card.select(".tag-item")
            tags = [t.get_text(strip=True) for t in tag_els]
            description = " ".join(tags)

        total_price = 0
        price_el = card.select_one(".price")
        if price_el:
            price_text = price_el.get_text(strip=True)
            total_price = self.parse_price(price_text)

        if total_price == 0:
            origin_price = card.select_one(".origin-price")
            if origin_price:
                total_price = self.parse_price(origin_price.get_text(strip=True))

        if total_price == 0:
            price_wrapper = card.select_one(".price-wrapper")
            if price_wrapper:
                ptext = price_wrapper.get_text(" ", strip=True)
                prices = re.findall(r"([\d,]+)", ptext)
                for p in prices:
                    try:
                        v = float(p.replace(",", ""))
                        if PRICE_MIN <= v <= PRICE_MAX:
                            total_price = v
                            break
                    except:
                        pass

        unit_price = 0
        if area_ping > 0 and total_price > 0:
            unit_price = round(total_price / area_ping, 2)

        img_url = ""
        if img:
            img_url = img.get("src", "") or img.get("data-src", "")

        return {
            "title": title, "address": address, "district": "",
            "total_price": total_price, "unit_price": unit_price,
            "area_ping": area_ping, "rooms": rooms, "halls": halls,
            "baths": baths, "building_age": building_age,
            "building_type": building_type, "floor": floor,
            "image_urls": img_url, "floorplan_url": "",
            "url": f"{self.BASE_URL}/house/{house_id}",
            "description": description[:200], "listed_date": "",
            "house_id": house_id,
        }
