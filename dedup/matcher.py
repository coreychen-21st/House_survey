from dedup.address_norm import address_fingerprint
from storage.database import (
    get_db, find_similar_by_address, delete_listing,
    listing_exists, insert_listing, get_new_listings, mark_notified
)


def deduplicate_cross_source(listings):
    """
    跨站去重：
    1. 相同 address_hash → 保留總價最低的
    2. 相同 image_hash → 保留總價最低的（輔助）
    """
    grouped = {}
    for item in listings:
        addr_hash = item.get("address_hash", "")
        img_hash = item.get("image_hash", "")

        key = addr_hash if addr_hash else f"img:{img_hash}" if img_hash else f"url:{item.get('url', id(item))}"

        if key not in grouped:
            grouped[key] = item
        else:
            existing = grouped[key]
            if item.get("total_price", 0) < existing.get("total_price", 0):
                grouped[key] = item

    deduped = list(grouped.values())
    deduped.sort(key=lambda x: x.get("total_price", 0))
    return deduped


def merge_and_deduplicate(all_listings):
    """
    合併所有來源 + 跨站去重 + 與歷史資料比對
    """
    if not all_listings:
        return []

    deduped = deduplicate_cross_source(all_listings)

    final = []
    for item in deduped:
        addr_hash = item.get("address_hash", "")
        if addr_hash:
            existing = find_similar_by_address(addr_hash)
            if existing:
                existing_prices = [e["total_price"] for e in existing]
                if item["total_price"] >= min(existing_prices):
                    continue

        final.append(item)

    return final


def process_and_store(all_listings):
    deduped = merge_and_deduplicate(all_listings)
    stored_ids = []
    for item in deduped:
        lid = insert_listing(item)
        if lid:
            stored_ids.append(lid)
    return stored_ids
