from .base import BaseCrawler
import httpx
from config.settings import MAX_PAGES


class HousePriceCrawler(BaseCrawler):
    source = "houseprice"

    BASE_URL = "https://buy.houseprice.tw"
    API_URL = "https://www.houseprice.tw/ws/buygetWebCase/"

    def crawl(self):
        results = []
        for page in range(1, MAX_PAGES + 1):
            print(f"[5168] 爬取第 {page} 頁")
            try:
                items = self._fetch_page(page)
                if not items:
                    break
                for item in items:
                    enriched = self.enrich_listing(item)
                    if self.basic_filter(enriched):
                        results.append(enriched)
                print(f"[5168] 第 {page} 頁: {len(items)} 筆")
                self.sleep()
            except Exception as e:
                print(f"[5168] 第 {page} 頁錯誤: {e}")
                break
        print(f"[5168] 總計 {len(results)} 筆")
        return results

    def _fetch_page(self, page):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Referer": "https://www.houseprice.tw/",
            "Origin": "https://www.houseprice.tw",
        }

        payload = {
            "City": "台北市",
            "LTotalPrice": 300,
            "HTotalPrice": 1300,
            "BuildPinMin": 19,
            "BuildAgeMax": 46,
            "Page": page,
            "Rows": 30,
        }

        resp = httpx.post(self.API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        cases = data.get("webCaseGroupings", [])
        items = []
        for case in cases:
            item = self._parse_case(case)
            if item:
                items.append(item)
        return items

    def _parse_case(self, case):
        if not isinstance(case, dict):
            return None

        sid = case.get("sid", "")
        title = case.get("caseName", "")
        address = case.get("simpAddress", "")
        total_price = self._num(case.get("totalPrice"))
        area_ping = self._num(case.get("buildPin"))
        building_age = self._num(case.get("buildAge"))
        building_type = case.get("caseTypeName", "")
        rooms = int(self._num(case.get("rm", 0)))
        halls = 0
        baths = 0

        floor_str = ""
        from_floor = case.get("fromFloor", "")
        up_floor = case.get("upFloor", "")
        if from_floor:
            floor_str = f"{from_floor}" if not up_floor else f"{from_floor}/{up_floor}"

        img_urls = []
        images = case.get("imageFileList", [])
        if images:
            for img in images:
                url = img.get("casePicUrl", "") if isinstance(img, dict) else str(img)
                if url:
                    img_urls.append(url)
        pic = case.get("picUrl", "")
        if pic and not pic.startswith("http") and "." not in pic:
            pic = ""
        if pic and not pic.startswith(("http://", "https://")):
            pic = f"https:{pic}" if pic.startswith("//") else f"https://{pic}"
        if pic and pic not in img_urls:
            img_urls.insert(0, pic)
        img_urls_str = ",".join(img_urls[:10])

        unit_price = 0
        if area_ping > 0 and total_price > 0:
            unit_price = round(total_price / area_ping, 2)

        listed_date = case.get("newKeyInDate", "")
        group_count = case.get("groupCount", 0)
        if group_count > 1:
            title = f"{title} (共{group_count}筆)"

        return {
            "title": title, "address": address, "district": "",
            "total_price": total_price, "unit_price": unit_price,
            "area_ping": area_ping, "rooms": rooms, "halls": halls,
            "baths": baths, "building_age": building_age,
            "building_type": building_type, "floor": floor_str,
            "image_urls": img_urls_str, "floorplan_url": "",
            "url": f"{self.BASE_URL}/house/{sid}" if sid else "",
            "description": "", "listed_date": str(listed_date),
            "house_id": str(sid),
        }

    def _num(self, val):
        if val is None or val == "":
            return 0
        if isinstance(val, (int, float)):
            return float(val)
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0
