from __future__ import annotations

import concurrent.futures
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_image(product: dict) -> tuple | None:
    try:
        request = urllib.request.Request(
            product["image"],
            headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-1023"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            content_type = response.headers.get("Content-Type", "")
            response.read(32)
            if response.status in (200, 206) and content_type.startswith("image/"):
                return None
            return product["id"], response.status, content_type, product["image"]
    except Exception as error:
        return product["id"], type(error).__name__, str(error)[:120], product["image"]


source = (ROOT / "catalog-data.js").read_text(encoding="utf-8")
products = json.loads(source[source.index("=") + 1 :].strip().rstrip(";"))
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
    failures = [result for result in executor.map(check_image, products) if result]
print(json.dumps({"checked": len(products), "bad_count": len(failures), "bad": failures}, ensure_ascii=False))
