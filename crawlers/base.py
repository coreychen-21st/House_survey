import re
import time
from config.settings import (
    PRICE_MIN, PRICE_MAX, MIN_AREA_PING, MIN_ROOMS,
    MAX_BUILDING_AGE, NEGATIVE_KEYWORDS, REQUEST_DELAY
)
from dedup.address_norm import normalize_address, address_fingerprint
from dedup.image_hash import compute_aggregate_hash


class BaseCrawler:
    source = "base"

    def parse_price(self, text):
        text = str(text).replace(",", "").replace("萬", "").strip()
        try:
            return float(text)
        except ValueError:
            return 0

    def parse_area(self, text):
        text = str(text).replace("坪", "").strip()
        try:
            return float(text)
        except ValueError:
            return 0

    def parse_age(self, text):
        text = str(text).replace("年", "").strip()
        try:
            return float(text)
        except ValueError:
            return 0

    def parse_rooms(self, text):
        m = re.search(r"(\d+)\s*房", str(text))
        return int(m.group(1)) if m else 0

    def parse_halls(self, text):
        m = re.search(r"(\d+)\s*廳", str(text))
        return int(m.group(1)) if m else 0

    def parse_baths(self, text):
        m = re.search(r"(\d+\.?\d*)\s*衛", str(text))
        return float(m.group(1)) if m else 0

    def contains_negative_keywords(self, text):
        text_lower = str(text).lower()
        for kw in NEGATIVE_KEYWORDS:
            if kw in text_lower or kw in str(text):
                return True
        return False

    def basic_filter(self, data):
        total_price = data.get("total_price", 0)
        if total_price < PRICE_MIN or total_price > PRICE_MAX:
            return False

        area_ping = data.get("area_ping", 0)
        if area_ping < MIN_AREA_PING:
            return False

        rooms = data.get("rooms", 0)
        if rooms < MIN_ROOMS and rooms != 0:
            return False

        building_age = data.get("building_age", 0)
        if building_age > MAX_BUILDING_AGE and building_age > 0:
            return False

        if self.contains_negative_keywords(data.get("title", "")):
            return False
        if self.contains_negative_keywords(data.get("description", "")):
            return False

        return True

    def basic_filter_debug(self, data):
        total_price = data.get("total_price", 0)
        if total_price < PRICE_MIN or total_price > PRICE_MAX:
            return False, f"price={total_price}"
        area_ping = data.get("area_ping", 0)
        if area_ping < MIN_AREA_PING:
            return False, f"area={area_ping}"
        rooms = data.get("rooms", 0)
        if rooms < MIN_ROOMS and rooms != 0:
            return False, f"rooms={rooms}"
        building_age = data.get("building_age", 0)
        if building_age > MAX_BUILDING_AGE and building_age > 0:
            return False, f"age={building_age}"
        if self.contains_negative_keywords(data.get("title", "")):
            return False, "negative_title"
        if self.contains_negative_keywords(data.get("description", "")):
            return False, "negative_desc"
        return True, ""

    def enrich_listing(self, data):
        data["source"] = self.source
        data["address_hash"] = address_fingerprint(
            data.get("address", ""),
            data.get("floor", ""),
            data.get("area_ping", 0)
        )
        if data.get("image_urls"):
            data["image_hash"] = compute_aggregate_hash(data["image_urls"])
        else:
            data["image_hash"] = ""
        return data

    def crawl(self):
        raise NotImplementedError

    def sleep(self):
        time.sleep(REQUEST_DELAY)
