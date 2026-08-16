from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote


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

# Only supplier categories that belong to the ALT-CAM assortment are public.
# This prevents unrelated office equipment from falling into the camera group.
ALLOWED_CATEGORY_IDS = {
    "cameras": {11, 13, 16, 18, 59, 63, 65, 67, 72, 155, 271},
    "recorders_storage": {12, 17, 271},
    "intercoms": {20, 21, 22, 23},
    "access_control": {25, 26, 27, 28, 29, 30, 31, 32, 64, 71, 268},
    "ajax_security": {11, 38, 39, 40, 41, 79, 82, 84, 158, 173},
    "backup_power": {46, 47, 87, 88, 163, 192, 200, 216, 217, 218, 237, 239, 263},
    "brackets_junction_boxes": {15, 24, 71, 200, 210, 266},
    "cables_connectors": {45, 239},
    "installation_consumables": {43, 44, 48, 194, 240},
    "accessories": {24, 42, 46, 71, 139, 194, 217},
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


def normalize_image_url(value: object) -> str:
    url = clean(value, 2000).replace("%25", "%")
    return quote(url, safe=":/%?&=+#,()[]")


def is_publishable(product: dict, group: str) -> bool:
    price = float(product.get("source_price_uah") or 0)
    image = clean(product.get("image_url"), 2000)
    return bool(
        int(product.get("category_id") or 0) in ALLOWED_CATEGORY_IDS[group]
        and
        product.get("in_stock")
        and product.get("catalog_id")
        and product.get("name_uk")
        and image
        and "�" not in image
        and 0 < price <= 100000
    )


def load_public_products(source: Path) -> list[dict]:
    products: list[dict] = []
    for group, (category, subcategory) in GROUPS.items():
        path = source / f"{group}.json"
        for item in json.loads(path.read_text(encoding="utf-8")):
            if not is_publishable(item, group):
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
                    "image": normalize_image_url(item["image_url"]),
                    "available": True,
                    "price": round(float(item["source_price_uah"]), 2),
                }
            )
    products.sort(key=lambda item: (item["category"], item["subcategory"], item["brand"], item["name"], item["id"]))
    return products
