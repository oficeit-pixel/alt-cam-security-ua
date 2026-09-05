from __future__ import annotations

import html
import json
import re
from pathlib import Path

from catalog_rules import clean, key_features, load_public_products, normalize_image_url, public_description


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "catalog-sync" / "output"
QUOTAS = {
    "Камери відеоспостереження": 7,
    "Відеореєстратори та накопичувачі": 4,
    "Домофони та викличні панелі": 4,
    "Системи контролю доступу": 3,
    "Ajax та охоронна сигналізація": 5,
    "Альтернативна енергетика": 3,
    "Літієві акумулятори": 3,
    "Зарядні пристрої": 2,
    "Аксесуари для енергосистем": 2,
    "Акумулятори та елементи живлення": 3,
    "Аварійне електроживлення": 4,
    "Адаптери та блоки живлення": 3,
    "Мережеве обладнання": 4,
    "Кабельна продукція": 5,
    "Кронштейни та монтажні коробки": 2,
    "Аксесуари та витратні матеріали для монтажу": 2,
    "Електрика": 1,
    "Інструменти": 1,
    "Аксесуари для систем безпеки": 2,
}


def yugtorg_category(item: dict) -> str:
    group = item["group"]
    title = f"{item.get('name_uk', '')} {item.get('model', '')}".casefold()
    if group == "security":
        if re.search(r"реєстратор|nvr|dvr|xvr|накопичувач", title):
            return "Відеореєстратори та накопичувачі"
        if re.search(r"домофон|викличн|відеопанел", title):
            return "Домофони та викличні панелі"
        if re.search(r"ajax|сигналіз|датчик|сирен|охорон", title):
            return "Ajax та охоронна сигналізація"
        if re.search(r"контрол|зчитувач|замок|турнікет|шлагбаум", title):
            return "Системи контролю доступу"
        return "Камери відеоспостереження"
    return {
        "alternative_energy": "Альтернативна енергетика",
        "lithium_batteries": "Літієві акумулятори",
        "batteries": "Акумулятори та елементи живлення",
        "battery_accessories": "Аксесуари для енергосистем",
        "emergency_power": "Аварійне електроживлення",
        "electrical": "Електрика",
        "cable_products": "Кабельна продукція",
        "network_equipment": "Мережеве обладнання",
        "tools": "Інструменти",
        "installation_accessories": "Аксесуари та витратні матеріали для монтажу",
        "power_adapters": "Адаптери та блоки живлення",
    }[group]


def public_name(value: object) -> str:
    name = clean(value, 220)
    name = re.sub(r",?\s*Q\d+\b", "", name, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", name).strip(" ,")


def load_yugtorg() -> list[dict]:
    path = OUTPUT / "yugtorg-draft" / "shortlist.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    products = []
    for item in rows:
        images = list(dict.fromkeys(
            normalize_image_url(value)
            for value in [item.get("image_url"), *(item.get("images") or [])]
            if value
        ))
        products.append({
            "id": item["catalog_id"],
            "sku": clean(item.get("sku") or item.get("model"), 100),
            "category": yugtorg_category(item),
            "subcategory": "",
            "brand": clean(item.get("brand") or "Інший виробник", 100),
            "name": public_name(item.get("name_uk")),
            "model": clean(item.get("model"), 150),
            "description": public_description(item.get("description_uk")) or "Характеристики уточнюються.",
            "features": key_features(item),
            "image": images[0],
            "images": images,
            "available": True,
            "price": round(float(item["retail_price_uah"]), 2),
            "source_supplier": "yugtorg",
        })
    return products


def identity(item: dict) -> str:
    return re.sub(r"[^a-zа-яіїєґ0-9]+", "", f"{item.get('brand', '')}{item.get('model', '')}".casefold())


def balanced_selection(viatec: list[dict], yugtorg: list[dict]) -> list[dict]:
    for item in viatec:
        item["source_supplier"] = "viatec"
    selected, seen = [], set()
    for category, quota in QUOTAS.items():
        left = [item for item in yugtorg if item["category"] == category]
        right = [item for item in viatec if item["category"] == category]
        pool = [item for pair in zip(left, right) for item in pair] + left[len(right):] + right[len(left):]
        for item in pool:
            key = identity(item)
            if key and key not in seen:
                selected.append(item)
                seen.add(key)
            if sum(row["category"] == category for row in selected) >= quota:
                break
    remaining = [item for pair in zip(yugtorg, viatec) for item in pair] + yugtorg[len(viatec):] + viatec[len(yugtorg):]
    for item in remaining:
        key = identity(item)
        if key and key not in seen:
            selected.append(item)
            seen.add(key)
        if len(selected) == 60:
            break
    return selected[:60]


def main() -> None:
    products = balanced_selection(load_public_products(OUTPUT / "normalized"), load_yugtorg())
    target = OUTPUT / "storefront-approval.json"
    target.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = []
    for item in products:
        title = html.escape(item["name"])
        cards.append(
            f'<article><img src="{html.escape(item["image"], quote=True)}" alt="{title}" loading="lazy">'
            f'<div><small>{html.escape(item["category"])}</small><h2>{title}</h2>'
            f'<p>{html.escape(item["brand"])} · {html.escape(item["model"])}</p>'
            f'<strong>{float(item["price"]):,.0f} ₴</strong></div></article>'
        )
    page = """<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ALT-CAM · Єдиний каталог</title><style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#121212;color:#f5f5f7;font:15px Arial,sans-serif}main{width:min(1280px,calc(100% - 32px));margin:auto;padding:40px 0}h1{font-size:clamp(30px,5vw,56px);margin:0 0 8px}header p{color:#999}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:28px}article{overflow:hidden;border:1px solid #34343a;border-radius:14px;background:#1b1b1f}img{display:block;width:100%;height:220px;padding:14px;background:#fff;object-fit:contain}article>div{padding:16px}small{color:#ffcc00}h2{min-height:58px;font-size:17px;line-height:1.3}p{min-height:36px;color:#aaa}strong{display:block;margin-top:10px}@media(max-width:950px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.grid{grid-template-columns:1fr}}</style></head><body><main><header><h1>Єдиний каталог ALT-CAM</h1><p>Фінальна перевірка перед однаковою публікацією на сайті та у Facebook.</p></header><section class="grid">""" + "".join(cards) + "</section></main></body></html>"
    (OUTPUT / "storefront-approval.html").write_text(page, encoding="utf-8")
    print(json.dumps({"products": len(products), "json": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
