import re
import json
import httpx
from bs4 import BeautifulSoup
from .base import BaseCrawler
from config.settings import MAX_PAGES


class SinyiCrawler(BaseCrawler):
    source = "sinyi"
    BASE_URL = "https://www.sinyi.com.tw"

    def crawl(self):
        results = []
        for page in range(1, 51):
            print(f"[信義] 爬取第 {page} 頁")
            try:
                html = self._fetch(page)
                if not html:
                    break
                items = self._parse_all(html, page)
                if not items:
                    break
                for item in items:
                    enriched = self.enrich_listing(item)
                    if self.basic_filter(enriched):
                        results.append(enriched)
                print(f"[信義] 第 {page} 頁: {len(items)} 筆")
                self.sleep()
            except Exception as e:
                print(f"[信義] 第 {page} 頁錯誤: {e}")
                break
        print(f"[信義] 總計 {len(results)} 筆")
        return results

    def _fetch(self, page):
        params = {
            "region": "taipei-city", "price-min": "300", "price-max": "1300",
            "age-max": "46", "area-min": "19", "room-min": "2"
        }
        if page > 1:
            params["page"] = str(page)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = httpx.get(
            f"{self.BASE_URL}/buy/list", params=params,
            headers=headers, timeout=30, follow_redirects=True
        )
        if resp.status_code != 200:
            return None
        return resp.text

    def _parse_all(self, html, page):
        items = []

        # 1. Parse JSON "list" (精選推薦)
        json_items = self._parse_json_list(html)
        if json_items:
            items.extend(json_items)

        # 2. Parse HTML listing cards (SSR 渲染的搜尋結果)
        html_items = self._parse_html_cards(html)
        if html_items:
            items.extend(html_items)

        # 3. Parse JSON-LD structured data
        soup = BeautifulSoup(html, "lxml")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict) and "@type" in data:
                    if data.get("@type") == "ItemList" and "itemListElement" in data:
                        for elem in data["itemListElement"]:
                            if elem.get("@type") == "ListItem":
                                item = self._parse_ld_item(elem)
                                if item:
                                    items.append(item)
            except:
                pass

        seen_ids = set()
        unique = []
        for item in items:
            hid = item.get("house_id", "")
            if hid and hid in seen_ids:
                continue
            seen_ids.add(hid)
            unique.append(item)

        return unique

    def _parse_json_list(self, html):
        items = []
        m = re.search(r'"list"\s*:\s*\[', html)
        if not m:
            return items
        start = m.start() + len('"list":[')
        depth, pos, in_string = 1, start, False
        while depth > 0 and pos < len(html):
            c = html[pos]
            if c == '\\': pos += 1
            elif c == '"' and html[pos-1] != '\\': in_string = not in_string
            elif not in_string:
                if c == '[': depth += 1
                elif c == ']': depth -= 1
            pos += 1
        raw = f"[{html[start:pos-1]}]"
        try:
            data = json.loads(raw)
        except:
            return items
        for obj in data:
            if isinstance(obj, dict):
                item = self._parse_json_obj(obj)
                if item:
                    items.append(item)
        return items

    def _parse_json_obj(self, obj):
        name = obj.get("name", "")
        address = obj.get("address", "")
        total_price = self._safe_float(obj.get("totalPrice", 0))
        area_ping = self._safe_float(obj.get("areaBuilding", 0))
        building_age = self._safe_float(obj.get("age", 0))
        building_type = obj.get("houselandtypeShow", "")
        floor = str(obj.get("floor", ""))
        total_floor = str(obj.get("totalfloor", ""))
        floor_str = f"{floor}/{total_floor}" if floor and total_floor else floor

        layout = obj.get("layout", "") or ""
        rooms = self.parse_rooms(layout)
        halls = self.parse_halls(layout)
        baths = self.parse_baths(layout)

        images = obj.get("image", [])
        img_urls = ",".join([str(i) for i in images[:10]]) if isinstance(images, list) else str(images)

        unit_price = self._safe_float(obj.get("uniPrice", 0))
        if not unit_price and area_ping and total_price:
            unit_price = round(total_price / area_ping, 2)

        house_id = obj.get("houseNo", "")
        url = obj.get("shareURL", "") or f"{self.BASE_URL}/buy/detail/{house_id}"

        tags = obj.get("tags", [])
        description = " ".join([str(t) for t in tags]) if isinstance(tags, list) else ""

        return {
            "title": name, "address": address, "district": "",
            "total_price": total_price, "unit_price": unit_price,
            "area_ping": area_ping, "rooms": rooms, "halls": halls,
            "baths": baths, "building_age": building_age,
            "building_type": building_type, "floor": floor_str,
            "image_urls": img_urls, "floorplan_url": "",
            "url": url, "description": description[:300],
            "listed_date": "", "house_id": house_id,
        }

    def _parse_ld_item(self, item):
        name = item.get("name", "")
        url = item.get("url", "")
        image = item.get("image", "")
        house_id = re.search(r"/(\d+)", url or "").group(1) if url else ""
        return {
            "title": name, "address": "", "district": "",
            "total_price": 0, "unit_price": 0, "area_ping": 0,
            "rooms": 0, "halls": 0, "baths": 0, "building_age": 0,
            "building_type": "", "floor": "", "image_urls": image,
            "floorplan_url": "", "url": url, "description": "",
            "listed_date": "", "house_id": house_id,
        }

    def _parse_html_cards(self, html):
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen = set()

        for tag in soup.select("[class*='item'], [class*='card'], [class*='listing'], li"):
            text = tag.get_text(" ", strip=True)
            if "坪" not in text or "萬" not in text or len(text) < 40:
                continue

            title_el = tag.select_one("[class*='title'], h3, .title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title or title in seen:
                continue
            seen.add(title)

            addr_el = tag.select_one("[class*='address'], [class*='addr']")
            address = addr_el.get_text(strip=True) if addr_el else ""

            img = tag.select_one("img")
            img_url = img.get("src", "") or img.get("data-src", "") if img else ""

            link = tag.select_one("a[href]")
            href = link.get("href", "") if link else ""
            m = re.search(r"/buy/detail/(\w+)", href)
            house_id = m.group(1) if m else ""

            total_price = 0
            prices = re.findall(r"([\d,]+)\s*萬", text)
            for p in prices:
                try:
                    v = float(p.replace(",", ""))
                    if 300 <= v <= 1300:
                        total_price = v
                        break
                except:
                    pass

            area_ping = 0
            area_m = re.search(r"([\d.]+)坪", text)
            if area_m:
                area_ping = float(area_m.group(1))

            rooms = self.parse_rooms(text)
            halls = self.parse_halls(text)
            baths = self.parse_baths(text)

            building_age = 0
            age_m = re.search(r"([\d.]+)\s*年", text)
            if age_m:
                building_age = float(age_m.group(1))

            building_type = ""
            for bt in ["公寓", "大樓", "華廈", "透天", "別墅", "套房", "辦公"]:
                if bt in text:
                    building_type = bt
                    break

            unit_price = 0
            up_m = re.search(r"([\d.]+)\s*萬\s*/\s*坪", text)
            if up_m:
                unit_price = float(up_m.group(1))
            elif area_ping and total_price:
                unit_price = round(total_price / area_ping, 2)

            items.append({
                "title": title, "address": address, "district": "",
                "total_price": total_price, "unit_price": unit_price,
                "area_ping": area_ping, "rooms": rooms, "halls": halls,
                "baths": baths, "building_age": building_age,
                "building_type": building_type, "floor": "",
                "image_urls": img_url, "floorplan_url": "",
                "url": f"{self.BASE_URL}{href}" if not href.startswith("http") else href,
                "description": "", "listed_date": "", "house_id": house_id,
            })
        return items

    def _safe_float(self, val):
        if val is None or val == 0 or val == "":
            return 0
        if isinstance(val, (int, float)):
            return float(val)
        try:
            return float(str(val).replace(",", "").replace("萬", ""))
        except:
            return 0
