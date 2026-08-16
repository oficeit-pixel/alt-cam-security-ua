from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.parse import quote

from catalog_rules import load_public_products


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "catalog-sync" / "output" / "normalized"
OUTPUT = ROOT / "feeds" / "meta-catalog.csv"
SITE = "https://alt-cam.net.ua/catalog.html"


def main() -> None:
    rows = []
    for product in load_public_products(NORMALIZED):
        rows.append(
            {
                "id": product["id"],
                "title": product["name"],
                "description": product["description"],
                "availability": "in stock",
                "condition": "new",
                "price": f"{product['price']:.2f} UAH",
                "link": f"{SITE}?product={quote(product['id'])}",
                "image_link": product["image"],
                "brand": product["brand"],
                "product_type": product["category"],
                "custom_label_0": product["category"],
                "custom_label_1": "",
                "custom_label_2": "ALT-CAM retail",
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
