import json
from playwright.sync_api import sync_playwright
from .base import BaseCrawler
from config.settings import MAX_PAGES


class HousePriceCrawler(BaseCrawler):
    source = "houseprice"
    BASE_URL = "https://buy.houseprice.tw"
    API_URL = "https://www.houseprice.tw/ws/buygetWebCase/"

    def crawl(self):
        print("[5168] 正在使用 Playwright 渲染爬取...")
        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                }
            )
            page = context.new_page()
            try:
                page.goto("https://www.houseprice.tw/", timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                html = page.content()
                if self.is_blocked_page(html, page.title()):
                    print("[5168] 偵測到 403/CloudFront 封鎖，快速停止")
                    browser.close()
                    print(f"[5168] 總計 {len(results)} 筆")
                    return results
            except Exception as e:
                print(f"[5168] 首頁檢查失敗: {e}")
                browser.close()
                print(f"[5168] 總計 {len(results)} 筆")
                return results

            empty_count = 0
            for pg in range(1, MAX_PAGES + 1):
                if empty_count >= 3:
                    break
                print(f"[5168] 爬取第 {pg} 頁")

                try:
                    items = self._fetch_page_api(page, pg)
                    if not items:
                        empty_count += 1
                        continue

                    count_before = len(results)
                    for item in items:
                        enriched = self.enrich_listing(item)
                        if self.basic_filter(enriched):
                            results.append(enriched)
                    added = len(results) - count_before
                    print(f"[5168] 第 {pg} 頁: {len(items)} 筆, 過濾後 +{added} 筆")
                    if added == 0 and len(items) > 0:
                        empty_count += 1
                    else:
                        empty_count = max(0, empty_count - 1)
                    self.sleep()

                except Exception as e:
                    print(f"[5168] 第 {pg} 頁錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    break

            browser.close()

        print(f"[5168] 總計 {len(results)} 筆")
        return results

    def _fetch_page_api(self, page, pg):
        payload = {
            "City": "台北市",
            "LTotalPrice": 300,
            "HTotalPrice": 1300,
            "Page": pg,
            "Rows": 30,
        }

        result = page.evaluate("""
            async ([apiUrl, payload]) => {
                try {
                    const resp = await fetch(apiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json, text/plain, */*',
                            'Referer': 'https://www.houseprice.tw/',
                            'Origin': 'https://www.houseprice.tw',
                        },
                        body: JSON.stringify(payload),
                    });
                    const text = await resp.text();
                    return {status: resp.status, body: text, fetch_error: ''};
                } catch (e) {
                    return {status: 0, body: '', fetch_error: String(e)};
                }
            }
        """, [self.API_URL, payload])

        if result.get("fetch_error"):
            print(f"  API fetch error: {result.get('fetch_error')}")
            return []

        print(f"  API POST via browser → HTTP {result.get('status')}, response length={len(result.get('body', ''))}")

        if result.get("status") != 200:
            return []

        try:
            data = json.loads(result["body"])
        except Exception as e:
            print(f"  JSON parse error: {e}, raw={result.get('body', '')[:300]}")
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
