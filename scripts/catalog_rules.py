from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote


GROUPS = {
    "cameras": "Камери відеоспостереження",
    "recorders_storage": "Відеореєстратори та накопичувачі",
    "intercoms": "Домофони та викличні панелі",
    "access_control": "Системи контролю доступу",
    "ajax_security": "Ajax та охоронна сигналізація",
    "backup_power": "Резервне живлення",
    "brackets_junction_boxes": "Кронштейни та монтажні коробки",
    "cables_connectors": "Кабель для систем безпеки",
    "installation_consumables": "Монтажні матеріали",
    "accessories": "Аксесуари для систем безпеки",
}

# Only supplier categories that belong to the ALT-CAM assortment are public.
# This prevents unrelated office equipment from falling into the camera group.
ALLOWED_CATEGORY_IDS = {
    "cameras": {11, 13, 16, 18, 59, 63, 65, 67, 72, 155, 271},
    "recorders_storage": {12, 17, 271},
    "intercoms": {20, 21, 22, 23},
    "access_control": {25, 26, 27, 28, 29, 30, 31, 32, 64, 71, 268},
    "ajax_security": {11, 38, 39, 40, 41, 84},
    "backup_power": {46, 47, 87, 88, 163, 192, 200, 216, 217, 218, 237, 239, 263},
    "brackets_junction_boxes": {15, 24, 71, 200, 210, 266},
    "cables_connectors": {45, 239},
    "installation_consumables": {43, 44, 48, 194, 240},
    "accessories": {24, 42, 46, 71, 217},
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
    return "Інший виробник"


def normalize_image_url(value: object) -> str:
    url = clean(value, 2000).replace("%25", "%")
    return quote(url, safe=":/%?&=+#,()[]")


def public_category(group: str, product: dict) -> str:
    category_id = int(product.get("category_id") or 0)
    if group == "cameras" and category_id == 155:
        return "Комплекти відеоспостереження"
    if group == "intercoms" and category_id == 23:
        return "Комплекти домофонії"
    return GROUPS[group]


def public_description(value: object) -> str:
    description = clean(value, 5000)
    description = re.sub(r"https?://\S+|www\.\S+", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\b(?:Viatec|Югторг|Yugtorg|Nadzor)\b", "", description, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", description).strip()


def key_features(product: dict) -> list[str]:
    text = clean(
        " ".join(
            str(product.get(key) or "")
            for key in ("name_uk", "model", "description_uk", "properties")
        ),
        12000,
    )
    patterns = (
        r"\b\d+(?:[.,]\d+)?\s*(?:Мп|MP)\b",
        r"\b(?:ІЧ|ИК|IR)\s*(?:підсвічування\s*)?(?:до\s*)?\d+\s*м\b",
        r"\bIP\d{2}\b",
        r"\b(?:PoE|Wi[‑-]?Fi|HDCVI|HD[‑-]?TVI|AHD|ONVIF|ColorVu|AcuSense)\b",
        r"\b\d+(?:[.,]\d+)?\s*мм\b",
        r"\b\d+\s*(?:А·год|Аг|Ah|Вт|W)\b",
    )
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            value = clean(match, 32)
            if value and value.casefold() not in {item.casefold() for item in found}:
                found.append(value)
            if len(found) == 4:
                return found
    return found


def is_publishable(product: dict, group: str) -> bool:
    price = float(product.get("source_price_uah") or 0)
    image = clean(product.get("image_url"), 2000)
    category_id = int(product.get("category_id") or 0)
    title = f"{product.get('name_uk', '')} {product.get('model', '')}".lower()
    security_detector = bool(
        re.search(r"ajax|охорон|рух|відкрит|магнітоконтакт|розбит|вібрац|тривож|затоп", title)
    )
    retailer_brand = infer_brand(product).casefold() in {"viatec", "югторг", "yugtorg", "nadzor"}
    return bool(
        category_id in ALLOWED_CATEGORY_IDS[group]
        and (group != "ajax_security" or category_id != 39 or security_detector)
        and not retailer_brand
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
    for group in GROUPS:
        path = source / f"{group}.json"
        for item in json.loads(path.read_text(encoding="utf-8")):
            if not is_publishable(item, group):
                continue
            products.append(
                {
                    "id": clean(item["catalog_id"], 100),
                    "sku": clean(item.get("sku") or item.get("model") or item["catalog_id"], 100),
                    "category": public_category(group, item),
                    "subcategory": "",
                    "brand": infer_brand(item),
                    "name": clean(item.get("name_uk") or item.get("model") or "Обладнання", 200),
                    "model": clean(item.get("model"), 150),
                    "description": public_description(item.get("description_uk")) or "Характеристики уточнюються.",
                    "features": key_features(item),
                    "image": normalize_image_url(item["image_url"]),
                    "available": True,
                    "price": round(float(item["source_price_uah"]), 2),
                }
            )
    products.sort(key=lambda item: (item["category"], item["subcategory"], item["brand"], item["name"], item["id"]))
    return products
