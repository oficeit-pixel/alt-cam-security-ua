from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "catalog-sync" / "output" / "normalized"
OUTPUT = ROOT / "feeds" / "meta-catalog.csv"
SITE = "https://alt-cam.net.ua/"


def clean(value: object, limit: int) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def infer_brand(product: dict) -> str:
    brand = clean(product.get("brand"), 100)
    if brand:
        return brand
    haystack = f"{product.get('name_uk', '')} {product.get('model', '')}".lower()
    for candidate in ("Hikvision", "Dahua", "Ajax", "Imou", "Uniview", "NeoLight", "Full Energy", "Ritar"):
        if candidate.lower() in haystack:
            return candidate
    return "ALT-CAM"


def main() -> None:
    rows = []
    for path in sorted(NORMALIZED.glob("*.json")):
        products = json.loads(path.read_text(encoding="utf-8"))
        for product in products:
            price = product.get("source_price_uah")
            title = clean(product.get("name_uk"), 200)
            image = clean(product.get("image_url"), 2000)
            if not product.get("in_stock") or not price or price <= 0 or not title or not image:
                continue
            catalog_id = clean(product.get("catalog_id"), 100)
            sku = clean(product.get("sku"), 100)
            description = clean(product.get("description_uk"), 5000) or title
            rows.append(
                {
                    "id": catalog_id,
                    "title": title,
                    "description": description,
                    "availability": "in stock",
                    "condition": "new",
                    "price": f"{float(price):.2f} UAH",
                    "link": f"{SITE}?product={quote(sku)}#quiz",
                    "image_link": image,
                    "brand": infer_brand(product),
                    "custom_label_0": clean(product.get("group"), 100),
                    "custom_label_1": "ALT-CAM retail",
                }
            )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"file": str(OUTPUT), "products": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
