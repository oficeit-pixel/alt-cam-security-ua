import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "catalog-sync" / "output" / "normalized"
OUTPUT = ROOT / "catalog-data.js"

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


def quality(item):
    return (
        bool(item.get("brand")),
        bool(item.get("description_uk")),
        int(item.get("supplier_id") or 0),
    )


products = []
for group, (category, subcategory) in GROUPS.items():
    items = json.loads((SOURCE / f"{group}.json").read_text(encoding="utf-8"))
    candidates = [
        item for item in items
        if item.get("in_stock")
        and item.get("image_url")
        and 0 < float(item.get("source_price_uah") or 0) <= 100000
    ]
    candidates.sort(key=quality, reverse=True)
    for item in candidates[:20]:
        products.append({
            "id": item["catalog_id"],
            "sku": item.get("sku") or item.get("model") or item["catalog_id"],
            "category": category,
            "subcategory": subcategory,
            "brand": item.get("brand") or "Інший бренд",
            "name": item.get("name_uk") or item.get("model") or "Обладнання",
            "model": item.get("model") or "",
            "description": item.get("description_uk") or "Характеристики уточнюються.",
            "image": item["image_url"],
            "available": True,
            "price": round(float(item.get("source_price_uah") or 0)),
        })

payload = "window.ALTCAM_CATALOG = " + json.dumps(products, ensure_ascii=False, indent=2) + ";\n"
OUTPUT.write_text(payload, encoding="utf-8")
print(f"Created {OUTPUT.name}: {len(products)} products")
