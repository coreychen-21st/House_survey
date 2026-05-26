import hashlib
import httpx
from io import BytesIO
from PIL import Image
import imagehash


def compute_image_hash(image_url):
    if not image_url or not image_url.startswith("http"):
        return None
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(image_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if resp.status_code != 200:
                return None
            img = Image.open(BytesIO(resp.content))
            return str(imagehash.phash(img, hash_size=8))
    except Exception:
        return None


def compute_aggregate_hash(image_urls):
    if not image_urls:
        return ""

    urls = image_urls.split(",")[:3]
    hashes = []
    for url in urls:
        h = compute_image_hash(url.strip())
        if h:
            hashes.append(h)

    if not hashes:
        return ""

    combined = "|".join(sorted(hashes))
    return hashlib.md5(combined.encode()).hexdigest()[:16]
