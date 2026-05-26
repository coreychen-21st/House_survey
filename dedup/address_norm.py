import re
import hashlib


def normalize_address(address):
    if not address:
        return ""

    a = address.strip()

    replacements = {
        "臺北市": "台北市", "臺中市": "台中市", "臺南市": "台南市",
        "臺東縣": "台東縣", "臺": "台",
        "１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
        "６": "6", "７": "7", "８": "8", "９": "9", "０": "0",
        "之": "-", "Ｏ": "0",
        "１段": "一段", "２段": "二段", "３段": "三段", "４段": "四段",
        "５段": "五段", "６段": "六段", "７段": "七段", "８段": "八段",
        "９段": "九段", "１０段": "十段",
    }

    for old, new in replacements.items():
        a = a.replace(old, new)

    a = re.sub(r"\s+", "", a)
    a = re.sub(r"[^\w一二三四五六七八九十百千萬億段路街巷弄號樓之\-]", "", a)

    return a


def extract_segment(address):
    norm = normalize_address(address)
    patterns = [
        r"台北市(\S+?區)(\S+?路|\S+?街|\S+?大道|\S+?巷|\S+?弄)",
    ]
    for p in patterns:
        m = re.search(p, norm)
        if m:
            return m.group(1) + m.group(2)
    return norm[:20]


def address_fingerprint(address, floor="", area_ping=0):
    norm = normalize_address(address)
    floor_info = normalize_address(floor) if floor else ""
    area_bucket = round(area_ping / 3) * 3 if area_ping else 0
    combined = f"{norm}|{floor_info}|{area_bucket}"
    return hashlib.md5(combined.encode()).hexdigest()
