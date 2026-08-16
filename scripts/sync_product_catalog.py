from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "catalog-sync" / "config.json"
DEFAULT_OUTPUT = ROOT / "catalog-sync" / "output"


def text(node: ET.Element, name: str) -> str:
    value = node.findtext(name)
    return (value or "").strip()


def as_float(value: str) -> float | None:
    try:
        return round(float(value.replace(",", ".")), 2)
    except (TypeError, ValueError):
        return None


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "ALT-CAM-Catalog-Sync/1.0"})
    with urllib.request.urlopen(request, timeout=180) as source, target.open("wb") as out:
        shutil.copyfileobj(source, out)


def ancestry(category_id: int, categories: dict[int, dict]) -> list[int]:
    result, seen = [], set()
    current = category_id
    while current and current not in seen and current in categories:
        seen.add(current)
        result.append(current)
        current = categories[current]["parent_id"]
    return result


def altcam_group(category_id: int, categories: dict[int, dict], title: str) -> str:
    chain = ancestry(category_id, categories)
    names = " ".join(categories[item]["title"].lower() for item in chain if item in categories)
    haystack = f"{names} {title.lower()}"
    if category_id == 15 or any(x in haystack for x in ("кронштейн", "розподільч", "бокс монтаж")):
        return "brackets_junction_boxes"
    if category_id == 45 or any(x in haystack for x in ("кабель", "конектор", "роз'єм", "роз’єм")):
        return "cables_connectors"
    if any(x in haystack for x in ("інструмент", "тестер", "монтажний комплект", "монтаж оптики")):
        return "installation_consumables"
    if any(x in haystack for x in ("аксесуар", "адаптер", "перехідник")):
        return "accessories"
    if 185 in chain or any(x in haystack for x in ("дбж", "акумулятор", "живлення", "стабілізатор", "bess")):
        return "backup_power"
    if 5 in chain or "ajax" in haystack or "сигналіза" in haystack:
        return "ajax_security"
    if any(x in haystack for x in ("контроль доступ", "контролер", "зчитувач", "замок", "турнікет", "шлагбаум")):
        return "access_control"
    if 2 in chain or any(x in haystack for x in ("домофон", "викличн", "монітор")):
        return "intercoms"
    if any(x in haystack for x in ("реєстратор", "накопичувач", "жорстк", "відеосервер")):
        return "recorders_storage"
    return "cameras"


def altcam_group_v2(category_id: int, categories: dict[int, dict], title: str) -> str:
    """Stable Ukrainian mapping with explicit installation categories first."""
    chain = ancestry(category_id, categories)
    names = " ".join(categories[item]["title"].lower() for item in chain if item in categories)
    haystack = f"{names} {title.lower()}"
    if any(item in chain for item in (15, 210, 266)) or any(
        value in haystack for value in ("кронштейн", "монтажна коробка", "розподільча коробка", "бокс монтаж")
    ):
        return "brackets_junction_boxes"
    if any(item in chain for item in (45, 239)) or any(
        value in haystack for value in ("кабель", "конектор", "роз'єм", "роз’єм", "рознім")
    ):
        return "cables_connectors"
    if any(item in chain for item in (43, 44, 48)) or any(
        value in haystack for value in ("інструмент", "тестер", "монтажний комплект", "монтаж оптики", "витратні матеріали")
    ):
        return "installation_consumables"
    if 24 in chain or any(value in haystack for value in ("аксесуар", "адаптер", "перехідник")):
        return "accessories"
    if 185 in chain or any(value in haystack for value in ("дбж", "акумулятор", "живлення", "стабілізатор", "bess")):
        return "backup_power"
    if 5 in chain or "ajax" in haystack or "сигналіза" in haystack:
        return "ajax_security"
    if any(item in chain for item in (25, 26, 27, 28, 29, 30, 31, 32, 64, 71, 268)) or (
        2 not in chain
        and any(value in haystack for value in ("контроль доступу", "контролер", "зчитувач", "замок", "турнікет", "шлагбаум"))
    ):
        return "access_control"
    if any(item in chain for item in (20, 21, 22, 23)) or any(
        value in haystack for value in ("домофон", "виклична панель", "монітор домофона")
    ):
        return "intercoms"
    if any(item in chain for item in (12, 17)) or any(
        value in haystack for value in ("реєстратор", "накопичувач", "жорсткий диск", "відеосервер")
    ):
        return "recorders_storage"
    return "cameras"


def parse_viatec(xml_path: Path, output: Path, included_roots: set[int]) -> dict:
    categories: dict[int, dict] = {}
    products_by_group: dict[str, list[dict]] = {}
    stats = Counter()
    for event, elem in ET.iterparse(xml_path, events=("end",)):
        if elem.tag == "category":
            category_id = int(text(elem, "id") or 0)
            categories[category_id] = {
                "id": category_id,
                "parent_id": int(text(elem, "parent_id") or 0),
                "title": text(elem, "title"),
            }
            elem.clear()
        elif elem.tag == "product":
            stats["all_products"] += 1
            category_id = int(text(elem, "category_id") or 0)
            chain = ancestry(category_id, categories)
            if not included_roots.intersection(chain):
                elem.clear()
                continue
            stock_raw = text(elem, "stock").lower()
            source_price = as_float(text(elem, "price_uah"))
            group = altcam_group_v2(category_id, categories, text(elem, "title"))
            properties = {}
            properties_node = elem.find("properties")
            if properties_node is not None:
                for prop in list(properties_node):
                    key = prop.get("name") or prop.findtext("name") or prop.tag
                    value = prop.get("value") or prop.findtext("value") or (prop.text or "")
                    if key and value:
                        properties[str(key).strip()] = str(value).strip()
            product = {
                "catalog_id": f"viatec-{text(elem, 'id')}",
                "supplier": "viatec",
                "supplier_id": text(elem, "id"),
                "sku": text(elem, "code") or text(elem, "id"),
                "group": group,
                "category_id": category_id,
                "category": categories.get(category_id, {}).get("title", ""),
                "brand": text(elem, "brand"),
                "model": text(elem, "model"),
                "name_uk": text(elem, "title"),
                "description_uk": text(elem, "descr"),
                "image_url": text(elem, "image"),
                "supplier_url": text(elem, "url"),
                "in_stock": stock_raw not in {"", "no", "0", "false", "out"},
                "source_price_uah": source_price,
                "retail_price_uah": None,
                "publishable": False,
                "properties": properties,
            }
            products_by_group.setdefault(group, []).append(product)
            stats["selected_products"] += 1
            stats[f"group:{group}"] += 1
            stats["in_stock" if product["in_stock"] else "out_of_stock"] += 1
            stats["with_price" if source_price and source_price > 0 else "without_price"] += 1
            elem.clear()

    output.mkdir(parents=True, exist_ok=True)
    catalog_dir = output / "normalized"
    catalog_dir.mkdir(exist_ok=True)
    index = []
    for group, products in sorted(products_by_group.items()):
        path = catalog_dir / f"{group}.json"
        path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append({"group": group, "count": len(products), "file": f"normalized/{path.name}"})

    categories_path = output / "categories.json"
    categories_path.write_text(
        json.dumps(sorted(categories.values(), key=lambda item: item["id"]), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Viatec Ukrainian XML",
        "source_file_bytes": xml_path.stat().st_size,
        "groups": index,
        "stats": dict(sorted(stats.items())),
        "publication_status": "blocked_until_markup_rules_are_approved",
    }
    (output / "sync-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "catalog-summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group", "count", "file"])
        writer.writeheader()
        writer.writerows(index)
    return report


def save_yugtorg_probe(output: Path, api_base: str) -> None:
    api_key = os.getenv("YUGTORG_API_KEY", "").strip()
    status = {"configured": bool(api_key), "downloaded": False}
    if api_key:
        params = urllib.parse.urlencode({"apiKey": api_key, "level": 5, "lang": "ua"})
        target = output / "raw" / "yugtorg-categories.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        download(f"{api_base}/categories?{params}", target)
        status["downloaded"] = True
        status["bytes"] = target.stat().st_size
    (output / "yugtorg-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--viatec-file", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "raw"
    raw_dir.mkdir(exist_ok=True)
    if args.viatec_file:
        xml_path = args.viatec_file.resolve()
    else:
        xml_path = raw_dir / "viatec-product-info-uk.xml"
        download(config["viatec_feed_url"], xml_path)
    report = parse_viatec(xml_path, output, set(config["included_root_category_ids"]))
    save_yugtorg_probe(output, config["yugtorg_api_base"])
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
