"""Supplier stock lookup for order items (owner-only; purchase prices are never returned).

* Viatec: public Ukrainian XML feeds (catalog-sync/config.json -> viatec_feeds); <stock> is yes/few/no.
* Yugtorg: b2b API `product` market (needs YUGTORG_API_KEY); stock is in the `count` field.
Item ids follow the catalog convention `viatec-<id>` / `yugtorg-<id>`.
"""
from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientTimeout

from bot.config import get_settings

logger = logging.getLogger("altcam.supplier_stock")
CONFIG_PATH = Path(__file__).resolve().parents[2] / "catalog-sync" / "config.json"
VIATEC_STOCK_LABELS = {"yes": "є в наявності", "few": "мало (уточнити)", "no": "немає"}
_viatec_cache: dict[str, Any] = {"loaded_at": 0.0, "items": {}}
_viatec_lock = asyncio.Lock()


def viatec_feed_urls() -> list[str]:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(feed.get("url")) for feed in config.get("viatec_feeds", []) if str(feed.get("url", "")).startswith("https://")]


def parse_viatec_xml(path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "product":
            if elem.tag == "category":
                elem.clear()
            continue
        product_id = (elem.findtext("id") or "").strip()
        if product_id:
            result[product_id] = {
                "stock": (elem.findtext("stock") or "").strip().lower(),
                "url": (elem.findtext("url") or "").strip(),
                "code": (elem.findtext("code") or "").strip(),
            }
        elem.clear()
    return result


async def _download(client: ClientSession, url: str, target: Path) -> None:
    async with client.get(url) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            async for chunk in response.content.iter_chunked(1 << 16):
                handle.write(chunk)


async def load_viatec_stock(force: bool = False) -> dict[str, dict[str, str]]:
    ttl = get_settings().supplier_stock_ttl_minutes * 60
    async with _viatec_lock:
        if not force and _viatec_cache["items"] and time.monotonic() - _viatec_cache["loaded_at"] < ttl:
            return _viatec_cache["items"]
        items: dict[str, dict[str, str]] = {}
        async with ClientSession(timeout=ClientTimeout(total=180)) as client:
            with tempfile.TemporaryDirectory(prefix="altcam-viatec-") as temp:
                for index, url in enumerate(viatec_feed_urls()):
                    target = Path(temp) / f"feed-{index}.xml"
                    try:
                        await _download(client, url, target)
                        items.update(await asyncio.to_thread(parse_viatec_xml, target))
                    except Exception as exc:
                        logger.warning("viatec_feed_failed index=%s (%s)", index, type(exc).__name__)
                    finally:
                        target.unlink(missing_ok=True)
        if items:
            _viatec_cache.update(loaded_at=time.monotonic(), items=items)
        return items or _viatec_cache["items"]


def _find_count(payload: Any) -> Any:
    if isinstance(payload, dict):
        if "count" in payload:
            return payload["count"]
        for value in payload.values():
            found = _find_count(value)
            if found is not None:
                return found
    if isinstance(payload, list):
        for value in payload:
            found = _find_count(value)
            if found is not None:
                return found
    return None


def yugtorg_stock_label(value: Any) -> str:
    """Yugtorg count may be a number or '+'..'+++++' markers; empty/0/'-' = none."""
    text = str(value if value is not None else "").strip().casefold()
    if text in {"", "0", "-", "--", "---", "no", "none", "немає", "нет", "відсутній"}:
        return "немає"
    return f"є в наявності ({text})"


async def yugtorg_stock(product_id: str) -> str:
    settings = get_settings()
    if not settings.yugtorg_api_key:
        return "не налаштовано (YUGTORG_API_KEY)"
    query = urlencode({"apikey": settings.yugtorg_api_key, "id": product_id, "lang": "ua"})
    url = f"{settings.yugtorg_api_base.rstrip('/')}/product&{query}"
    try:
        async with ClientSession(timeout=ClientTimeout(total=20)) as client:
            async with client.get(url) as response:
                response.raise_for_status()
                payload = json.loads(await response.text())
    except Exception as exc:
        logger.warning("yugtorg_stock_failed (%s)", type(exc).__name__)
        return "помилка запиту — перевірте вручну"
    count = _find_count(payload)
    return "не знайдено у відповіді API" if count is None else yugtorg_stock_label(count)


async def check_items(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Returns [{id, name, supplier, stock, url}] for supplier items; other items are marked manual."""
    rows: list[dict[str, str]] = []
    viatec: dict[str, dict[str, str]] | None = None
    for item in items or []:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id", ""))
        supplier, _, supplier_id = item_id.partition("-")
        row = {"id": item_id, "name": str(item.get("name", ""))[:120], "supplier": supplier, "stock": "перевірити вручну", "url": ""}
        if supplier == "viatec" and supplier_id:
            if viatec is None:
                viatec = await load_viatec_stock()
            found = viatec.get(supplier_id)
            if found:
                row["stock"] = VIATEC_STOCK_LABELS.get(found["stock"], found["stock"] or "невідомо")
                row["url"] = found["url"]
            else:
                row["stock"] = "немає у фіді (знято/невідомо)"
        elif supplier == "yugtorg" and supplier_id:
            row["stock"] = await yugtorg_stock(supplier_id)
        rows.append(row)
    return rows
