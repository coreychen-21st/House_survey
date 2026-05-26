import re
import httpx
from bs4 import BeautifulSoup
from .base import BaseCrawler
from config.settings import MAX_PAGES


class YungChingCrawler(BaseCrawler):
    source = "yungching"
    BASE_URL = "https://buy.yungching.com.tw"

    def crawl(self):
        results = []
        for page in range(1, MAX_PAGES + 1):
            url = self._build_url(page)
            print(f"[永慶] 爬取第 {page} 頁")
            try:
                items = self._fetch_and_parse(url)
                if not items:
                    continue
                for item in items:
                    enriched = self.enrich_listing(item)
                    if self.basic_filter(enriched):
                        results.append(enriched)
                print(f"[永慶] 第 {page} 頁: {len(items)} 筆, 過濾後 {sum(1 for i in items if self.basic_filter(self.enrich_listing(i)))} 筆")
            except Exception as e:
                print(f"[永慶] 第 {page} 頁錯誤: {e}")
                import traceback
                traceback.print_exc()
                break
            self.sleep()
        print(f"[永慶] 總計 {len(results)} 筆")
        return results

    def _build_url(self, page):
        base = f"{self.BASE_URL}/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_"
        if page == 1:
            return base
        return base + f"?pg={page}"

    def _fetch_and_parse(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")

        cards = soup.select("a.link[href*='house/']")
        if not cards:
            cards = soup.select("a[href*='house/']")
        if not cards:
            cards = soup.find_all("a", href=re.compile(r"house/\d+"))

        print(f"  找到 {len(cards)} 個卡片")
        items = []
        for card in cards:
            href = card.get("href", "")
            m = re.search(r"house/(\d+)", href)
            if not m:
                continue
            house_id = m.group(1)
            item = self._parse_card(card, house_id)
            if item:
                items.append(item)
        return items

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
                        if 300 <= v <= 1300:
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
