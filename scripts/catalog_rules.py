from __future__ import annotations

import json
import re
from pathlib import Path


GROUPS = {
    "cameras": ("Відеоспостереження", "Камери"),
    "recorders_storage": ("Відеоспостереження", "Реєстратори та накопичувачі"),
    "intercoms": ("Домофонія та доступ", "Домофони"),
    "access_control": ("Домофонія та доступ", "Контроль доступу"),
    "ajax_security": ("Охоронні системи", "Ajax та сигналізація"),
    "backup_power": ("Резервне живлення", "ДБЖ, АКБ та інвертори"),
    "brackets_junction_boxes": ("Кронштейни та коробки", "Кронштейни та монтажні бокси"),
    "cables_connectors": ("Кабель та конектори", "Кабель, роз'єми та перехідники"),
    "installation_consumables": ("Монтажні матеріали", "Кріплення та витратні матеріали"),
    "accessories": ("Аксесуари", "Аксесуари"),
}


def clean(value: object, limit: int = 5000) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def infer_brand(product: dict) -> str:
    brand = clean(product.get("brand"), 100)
    if brand:
        return brand
    haystack = f"{product.get('name_uk', '')} {product.get('model', '')}".lower()
    for candidate in ("Hikvision", "Dahua", "Ajax", "Imou", "Uniview", "NeoLight", "Full Energy", "Ritar"):
        if candidate.lower() in haystack:
            return candidate
    return "ALT-CAM"


def is_publishable(product: dict) -> bool:
    price = float(product.get("source_price_uah") or 0)
    return bool(
        product.get("in_stock")
        and product.get("catalog_id")
        and product.get("name_uk")
        and product.get("image_url")
        and 0 < price <= 100000
    )


def load_public_products(source: Path) -> list[dict]:
    products: list[dict] = []
    for group, (category, subcategory) in GROUPS.items():
        path = source / f"{group}.json"
        for item in json.loads(path.read_text(encoding="utf-8")):
            if not is_publishable(item):
                continue
            products.append(
                {
                    "id": clean(item["catalog_id"], 100),
                    "sku": clean(item.get("sku") or item.get("model") or item["catalog_id"], 100),
                    "category": category,
                    "subcategory": subcategory,
                    "brand": infer_brand(item),
                    "name": clean(item.get("name_uk") or item.get("model") or "Обладнання", 200),
                    "model": clean(item.get("model"), 150),
                    "description": clean(item.get("description_uk"), 5000) or "Характеристики уточнюються.",
                    "image": clean(item["image_url"], 2000),
                    "available": True,
                    "price": round(float(item["source_price_uah"]), 2),
                }
            )
    products.sort(key=lambda item: (item["category"], item["subcategory"], item["brand"], item["name"], item["id"]))
    return products
