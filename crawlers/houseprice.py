from .base import BaseCrawler
import httpx
from config.settings import MAX_PAGES


class HousePriceCrawler(BaseCrawler):
    source = "houseprice"
    BASE_URL = "https://buy.houseprice.tw"
    API_URL = "https://www.houseprice.tw/ws/buygetWebCase/"

    def crawl(self):
        results = []
        empty_count = 0
        for page in range(1, MAX_PAGES + 1):
            if empty_count >= 3:
                break
            print(f"[5168] 爬取第 {page} 頁")
            try:
                items = self._fetch_page(page)
                if not items:
                    empty_count += 1
                    continue
                count_before = len(results)
                for item in items:
                    enriched = self.enrich_listing(item)
                    if self.basic_filter(enriched):
                        results.append(enriched)
                added = len(results) - count_before
                print(f"[5168] 第 {page} 頁: {len(items)} 筆, 過濾後 +{added} 筆")
                if added == 0 and len(items) > 0:
                    empty_count += 1
                else:
                    empty_count = max(0, empty_count - 1)
                self.sleep()
            except Exception as e:
                print(f"[5168] 第 {page} 頁錯誤: {e}")
                break
        print(f"[5168] 總計 {len(results)} 筆")
        return results

    def _fetch_page(self, page):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "https://www.houseprice.tw/",
            "Origin": "https://www.houseprice.tw",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
        payload = {
            "City": "台北市",
            "LTotalPrice": 300,
            "HTotalPrice": 1300,
            "Page": page,
            "Rows": 30,
        }
        resp = httpx.post(self.API_URL, json=payload, headers=headers, timeout=30)
        print(f"  API POST → HTTP {resp.status_code}, response length={len(resp.text)}")
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception as e:
            print(f"  JSON parse error: {e}, raw={resp.text[:300]}")
            return []
        cases = data.get("webCaseGroupings", [])
        total_count = data.get("count", data.get("totalCount", "unknown"))
        print(f"  API totalCount={total_count}, webCaseGroupings={len(cases)}")
        if not cases:
            print(f"  API keys: {list(data.keys())[:10]}")
            print(f"  API sample: {str(data)[:500]}")
        return [self._parse_case(c) for c in cases if isinstance(c, dict)]

    def _parse_case(self, case):
        sid = case.get("sid", "")
        title = case.get("caseName", "")
        address = case.get("simpAddress", "")
        total_price = self._num(case.get("totalPrice"))
        area_ping = self._num(case.get("buildPin"))
        building_age = self._num(case.get("buildAge"))
        building_type = case.get("caseTypeName", "")
        rooms = int(self._num(case.get("rm", 0)))
        from_floor = case.get("fromFloor", "")
        up_floor = case.get("upFloor", "")
        floor_str = f"{from_floor}" if not up_floor else f"{from_floor}/{up_floor}"

        img_urls = []
        images = case.get("imageFileList", []) or []
        for img in images:
            url = img.get("casePicUrl", "") if isinstance(img, dict) else str(img)
            if url:
                if not url.startswith("http"):
                    url = f"https:{url}" if url.startswith("//") else ""
                if url:
                    img_urls.append(url)

        pic = case.get("picUrl", "") or ""
        if pic and "." in pic and "/" in pic:
            if not pic.startswith("http"):
                pic = f"https:{pic}" if pic.startswith("//") else ""
            if pic and pic not in img_urls:
                img_urls.insert(0, pic)

        unit_price = 0
        if area_ping > 0 and total_price > 0:
            unit_price = round(total_price / area_ping, 2)

        return {
            "title": title, "address": address, "district": "",
            "total_price": total_price, "unit_price": unit_price,
            "area_ping": area_ping, "rooms": rooms, "halls": 0,
            "baths": 0, "building_age": building_age,
            "building_type": building_type, "floor": floor_str,
            "image_urls": ",".join(img_urls[:10]) if img_urls else "",
            "floorplan_url": "",
            "url": f"{self.BASE_URL}/house/{sid}" if sid else "",
            "description": case.get("newKeyInDate", ""),
            "listed_date": "", "house_id": str(sid),
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
