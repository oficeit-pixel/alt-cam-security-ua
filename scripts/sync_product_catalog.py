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
        return "cable_products"
    if any(x in haystack for x in ("інструмент", "тестер", "монтажний комплект", "монтаж оптики")):
        return "installation_consumables"
    if any(x in haystack for x in ("аксесуар", "адаптер", "перехідник")):
        return "accessories"
    if 185 in chain or any(x in haystack for x in ("дбж", "акумулятор", "живлення", "стабілізатор", "bess")):
        return "emergency_power"
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
        return "cable_products"
    if any(item in chain for item in (43, 44, 48)) or any(
        value in haystack for value in ("інструмент", "тестер", "монтажний комплект", "монтаж оптики", "витратні матеріали")
    ):
        return "installation_consumables"
    if 24 in chain or any(value in haystack for value in ("аксесуар", "адаптер", "перехідник")):
        return "accessories"
    if 185 in chain or any(value in haystack for value in ("дбж", "акумулятор", "живлення", "стабілізатор", "bess")):
        return "emergency_power"
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


FEED_CATEGORY_GROUPS: dict[str, dict[int, str]] = {
    "videonagliad": {
        **{item: "cameras" for item in (11, 13, 59, 60, 63, 65, 155)},
        **{item: "recorders_storage" for item in (12, 17)},
        **{item: "accessories" for item in (16, 18, 19, 53, 67, 72)},
    },
    "energosistemi": {
        **{item: "alternative_energy" for item in (163, 192, 200, 204, 218, 263)},
        237: "lithium_batteries",
        **{item: "chargers" for item in (138, 217)},
        194: "energy_accessories",
        **{item: "batteries" for item in (47, 216)},
        **{item: "emergency_power" for item in (87, 88, 233)},
        **{item: "power_adapters" for item in (46, 139)},
        239: "cable_products",
    },
    "video-intercoms": {
        **{item: "intercoms" for item in (20, 21, 22, 23, 24)},
        **{item: "access_control" for item in (25, 26, 27, 28, 29, 30, 31, 32, 64, 71, 268)},
    },
    "network": {item: "network_equipment" for item in (49, 50, 51, 52, 58, 70, 77, 140, 159, 270)},
    "alarms": {item: "ajax_security" for item in (38, 39, 40, 41, 42, 79, 82, 84, 158, 173)},
    "vse-dlia-montazhu": {
        **{item: "brackets_junction_boxes" for item in (15, 57, 210, 266)},
        45: "cable_products",
        **{item: "installation_consumables" for item in (43, 44, 48, 240)},
        72: "accessories",
    },
    "elektrika-ta-instrument": {
        **{item: "electrical" for item in (141, 171, 172, 193)},
        **{item: "tools" for item in (190, 196, 197)},
        **{item: "installation_consumables" for item in (219, 224)},
    },
}


def feed_group(feed_key: str, category_id: int) -> str | None:
    return FEED_CATEGORY_GROUPS.get(feed_key, {}).get(category_id)


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


def parse_viatec_feeds(feed_files: list[tuple[str, Path, str]], output: Path) -> dict:
    products_by_group: dict[str, list[dict]] = {}
    categories_all: dict[str, dict] = {}
    seen_products: set[str] = set()
    stats = Counter()
    source_reports = []

    for feed_key, xml_path, source_url in feed_files:
        categories: dict[int, dict] = {}
        feed_stats = Counter()
        for event, elem in ET.iterparse(xml_path, events=("end",)):
            if elem.tag == "category":
                category_id = int(text(elem, "id") or 0)
                category = {
                    "id": category_id,
                    "parent_id": int(text(elem, "parent_id") or 0),
                    "title": text(elem, "title"),
                    "source_feed": feed_key,
                }
                categories[category_id] = category
                categories_all[f"{feed_key}:{category_id}"] = category
                elem.clear()
                continue
            if elem.tag != "product":
                continue

            feed_stats["all_products"] += 1
            stats["all_products"] += 1
            category_id = int(text(elem, "category_id") or 0)
            group = feed_group(feed_key, category_id)
            if not group:
                feed_stats["excluded_unrelated"] += 1
                stats["excluded_unrelated"] += 1
                elem.clear()
                continue

            supplier_id = text(elem, "id")
            catalog_id = f"viatec-{supplier_id}"
            if not supplier_id or catalog_id in seen_products:
                feed_stats["duplicates"] += 1
                stats["duplicates"] += 1
                elem.clear()
                continue
            seen_products.add(catalog_id)

            properties = {}
            properties_node = elem.find("properties")
            if properties_node is not None:
                for prop in list(properties_node):
                    key = prop.get("name") or prop.findtext("name") or prop.tag
                    value = prop.get("value") or prop.findtext("value") or (prop.text or "")
                    if key and value:
                        properties[str(key).strip()] = str(value).strip()

            stock_raw = text(elem, "stock").lower()
            available_raw = text(elem, "available").lower()
            source_price = as_float(text(elem, "price_uah"))
            product = {
                "catalog_id": catalog_id,
                "supplier": "viatec",
                "supplier_id": supplier_id,
                "source_feed": feed_key,
                "source_url": source_url,
                "sku": text(elem, "code") or supplier_id,
                "group": group,
                "category_id": category_id,
                "category": categories.get(category_id, {}).get("title", ""),
                "brand": text(elem, "brand"),
                "model": text(elem, "model"),
                "name_uk": text(elem, "title"),
                "description_uk": text(elem, "descr"),
                "image_url": text(elem, "image"),
                "supplier_url": text(elem, "url"),
                "in_stock": stock_raw not in {"", "no", "0", "false", "out"} or available_raw in {"1", "yes", "true"},
                "source_price_uah": source_price,
                "retail_price_uah": None,
                "publishable": False,
                "properties": properties,
            }
            products_by_group.setdefault(group, []).append(product)
            feed_stats["selected_products"] += 1
            feed_stats["in_stock" if product["in_stock"] else "out_of_stock"] += 1
            feed_stats["with_image" if product["image_url"] else "without_image"] += 1
            feed_stats["with_description" if product["description_uk"] else "without_description"] += 1
            feed_stats["with_properties" if properties else "without_properties"] += 1
            feed_stats["with_price" if source_price and source_price > 0 else "without_price"] += 1
            stats["selected_products"] += 1
            stats[f"group:{group}"] += 1
            elem.clear()

        source_reports.append(
            {
                "key": feed_key,
                "url": source_url,
                "file_bytes": xml_path.stat().st_size,
                "stats": dict(sorted(feed_stats.items())),
            }
        )

    output.mkdir(parents=True, exist_ok=True)
    catalog_dir = output / "normalized"
    if catalog_dir.exists():
        shutil.rmtree(catalog_dir)
    catalog_dir.mkdir(exist_ok=True)
    index = []
    for group, products in sorted(products_by_group.items()):
        path = catalog_dir / f"{group}.json"
        path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append({"group": group, "count": len(products), "file": f"normalized/{path.name}"})

    (output / "categories.json").write_text(
        json.dumps(sorted(categories_all.values(), key=lambda item: (item["source_feed"], item["id"])), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Viatec Ukrainian thematic XML feeds",
        "sources": source_reports,
        "groups": index,
        "stats": dict(sorted(stats.items())),
        "publication_status": "validated_for_site_and_meta_generation",
    }
    (output / "sync-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "catalog-summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group", "count", "file"])
        writer.writeheader()
        writer.writerows(index)
    return report


def download_yugtorg_json(api_base: str, market: str, params: dict[str, object], target: Path) -> object:
    query = urllib.parse.urlencode(params)
    download(f"{api_base}/{market}&{query}", target)
    try:
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Yugtorg {market} endpoint returned non-JSON data") from exc
    if not isinstance(payload, (dict, list)):
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Yugtorg {market} endpoint returned an unsupported JSON structure")
    return payload


def save_yugtorg_probe(output: Path, api_base: str, draft_categories: dict[str, int]) -> None:
    api_key = os.getenv("YUGTORG_API_KEY", "").strip()
    status = {"configured": bool(api_key), "downloaded": False}
    if api_key:
        target = output / "raw" / "yugtorg-categories.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        download_yugtorg_json(api_base, "categories", {"apikey": api_key, "level": 5, "lang": "ua"}, target)
        first_category_id = next(iter(draft_categories.values()), None)
        if first_category_id:
            probe_target = output / "raw" / "yugtorg-products-probe.json"
            download_yugtorg_json(
                api_base,
                "products",
                {"apikey": api_key, "category": first_category_id, "noresize": 1, "limit": 2, "lang": "ua"},
                probe_target,
            )
            status["products_probe_bytes"] = probe_target.stat().st_size
        status["downloaded"] = True
        status["bytes"] = target.stat().st_size
    (output / "yugtorg-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--viatec-file", type=Path, help="Legacy single-feed override")
    parser.add_argument("--feed-dir", type=Path, help="Directory with <feed-key>.xml files")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "raw"
    raw_dir.mkdir(exist_ok=True)
    feed_files: list[tuple[str, Path, str]] = []
    if args.feed_dir:
        for feed in config["viatec_feeds"]:
            target = args.feed_dir.resolve() / f"{feed['key']}.xml"
            if not target.exists():
                raise FileNotFoundError(target)
            feed_files.append((feed["key"], target, feed["url"]))
    elif args.viatec_file:
        feed_files.append(("videonagliad", args.viatec_file.resolve(), "local-override"))
    else:
        for feed in config["viatec_feeds"]:
            local_file = str(feed.get("local_file", "")).strip()
            if local_file:
                target = Path(local_file).resolve()
                if not target.is_file():
                    raise FileNotFoundError(target)
            else:
                target = raw_dir / f"viatec-{feed['key']}.xml"
                download(feed["url"], target)
            feed_files.append((feed["key"], target, feed["url"]))
    report = parse_viatec_feeds(feed_files, output)
    if int(report.get("stats", {}).get("selected_products", 0)) < 20:
        raise RuntimeError("Catalog safety check failed: fewer than 20 relevant products")
    save_yugtorg_probe(output, config["yugtorg_api_base"], config.get("yugtorg_draft_categories", {}))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
