"""Read-only product catalog for the consultant: catalog-data.js (names/models/features) + feeds/meta-catalog.csv
prices (the same authoritative prices /api/orders uses) + manual price_overrides. Nothing here is invented:
products without a price are returned with price=None ("ціну уточнить менеджер")."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
CATALOG_JS = ROOT / "catalog-data.js"
CART_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
HIDDEN_BRANDS = re.compile(r"^(?:viatec|югторг|yugtorg|nadzor)$", re.I)
SYNONYMS = {
    "камера": "відеокамер", "камеру": "відеокамер", "камери": "відеокамер", "камер": "відеокамер",
    "реєстратор": "реєстратор", "регистратор": "реєстратор", "nvr": "nvr", "dvr": "dvr",
    "свитч": "комутатор", "switch": "комутатор", "коммутатор": "комутатор", "комутатор": "комутатор",
    "диск": "диск", "hdd": "hdd", "кабель": "кабель", "вита": "utp", "витая": "utp", "мп": "mp", "мпікс": "mp",
}


@dataclass
class Product:
    id: str
    name: str
    model: str
    brand: str
    category: str
    features: list[str] = field(default_factory=list)
    price: float | None = None
    text: str = ""

    def public(self, price: float | None = None, qty: int | None = None) -> dict[str, Any]:
        row = {"id": self.id, "title": f"{self.name} {self.model}".strip()[:160], "brand": self.brand,
               "category": self.category, "price_uah": price if price is not None else self.price,
               "link": f"https://alt-cam.net.ua/catalog.html?product={quote(self.id)}"}
        if self.features:
            row["features"] = self.features[:5]
        if qty is not None:
            row["qty"] = qty
        return row


def _csv_prices() -> dict[str, float]:
    from bot.web.site_leads import _feed_catalog

    try:
        return {key: price for key, (_, price) in _feed_catalog().items() if price > 0}
    except OSError:
        return {}


@lru_cache(maxsize=1)
def products() -> dict[str, Product]:
    source = CATALOG_JS.read_text(encoding="utf-8")
    data, _ = json.JSONDecoder().raw_decode(source, source.index("["))
    prices = _csv_prices()
    result: dict[str, Product] = {}
    for row in data:
        pid = str(row.get("id") or "")
        if not pid or HIDDEN_BRANDS.match(str(row.get("brand") or "")):  # same filter as catalog.js
            continue
        features = [str(x) for x in row.get("features") or []]
        product = Product(id=pid, name=str(row.get("name") or ""), model=str(row.get("model") or ""),
                          brand=str(row.get("brand") or ""), category=str(row.get("category") or ""),
                          features=features, price=prices.get(pid))
        product.text = " ".join([product.name, product.model, product.brand, product.category, *features]).lower()
        result[pid] = product
    return result


def _tokens(query: str) -> list[str]:
    words = re.findall(r"[\w.+-]+", (query or "").lower())
    return [SYNONYMS.get(w, w) for w in words if len(w) >= 2][:12]


def price_of(product: Product, overrides: dict[str, float] | None = None) -> float | None:
    if overrides and product.id in overrides:
        return float(overrides[product.id])
    return product.price


def search(query: str, *, category: str | None = None, max_price: float | None = None, limit: int = 8,
           overrides: dict[str, float] | None = None, catalog: dict[str, Product] | None = None) -> list[dict[str, Any]]:
    catalog = catalog if catalog is not None else products()
    tokens = _tokens(query)
    if not tokens:
        return []
    need = max(1, math.ceil(len(tokens) * 0.6))
    scored = []
    for product in catalog.values():
        if category and category.lower() not in product.category.lower():
            continue
        hits = sum(1 for t in tokens if t in product.text)
        if hits < need:
            continue
        price = price_of(product, overrides)
        if max_price is not None and (price is None or price > max_price):
            continue
        model_hits = sum(1 for t in tokens if t in product.model.lower())
        scored.append((-(hits + 2 * model_hits), price if price is not None else 1e12, product, price))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [p.public(price) for _, _, p, price in scored[:max(1, min(limit, 15))]]


def _number(pattern: str, text: str) -> int | None:
    values = [int(g) for m in re.finditer(pattern, text) for g in m.groups() if g]
    return max(values) if values else None


def channels(product: Product) -> int | None:
    return _number(r"(\d{1,2})\s*-?\s*(?:ch\b|х?\s*-?\s*кан)", f"{product.name} {product.model}".lower())


def ports(product: Product) -> int | None:
    """PoE port count: '16-портовий', 'з 4 портами POE', '8 PoE'."""
    text = f"{product.name} {product.model}".lower()
    return _number(r"(\d{1,2})\s*(?:-?\s*портов\w*|\s+порт\w*\s+poe|\s*poe)", text) or _number(r"(\d{1,2})\s*-?\s*порт", text)


_NVR_POE_COUNT = re.compile(r"(\d{1,2})\s*-?\s*poe(?!\s*:)", re.I)          # '8PoE', '24 PoE', '4-PoE'
_NVR_POE_MODEL = re.compile(r"[-/](\d{1,2})p(?=[-/(\s]|$)", re.I)          # DHI-NVR2108-8P-I2, DS-7108NI-Q1/8P(D)
_NVR_POE_SAME = re.compile(r"[-/]p(?=[-/(\s]|$)", re.I)                     # DHI-NVR1104HS-P-S3: PoE on every channel


def _own_text(product: Product) -> str:
    """Name/model/features only (category names contain generic words like 'PoE')."""
    return f"{product.name} {product.model} {' '.join(product.features)}".lower()


def is_poe_switch(product: Product) -> bool:
    text = _own_text(product)
    return "poe" in text and ("комутатор" in text or "коммутатор" in text or "switch" in text) \
        and "реєстратор" not in text and "nvr" not in text


def is_recorder(product: Product) -> bool:
    text = _own_text(product)
    return "nvr" in text or "відеореєстратор" in text or "реєстратор" in text


def nvr_poe_ports(product: Product) -> int:
    """Built-in PoE ports of a recorder (0 = no PoE, an external PoE switch is required).

    Explicit counts win ('8PoE', '-8P-', '/4P('); a bare '-P-' model suffix or a plain 'PoE' mark means PoE on every
    channel (Dahua/Hikvision naming)."""
    if not is_recorder(product):
        return 0
    head = f"{product.name} {product.model}"
    counts = [int(m.group(1)) for m in _NVR_POE_COUNT.finditer(head)]
    counts += [int(m.group(1)) for m in _NVR_POE_MODEL.finditer(product.model or "")]
    counts += [int(m.group(1)) for m in _NVR_POE_MODEL.finditer(product.name or "")]
    counts = [c for c in counts if 1 <= c <= 64]
    if counts:
        return max(counts)
    if _NVR_POE_SAME.search(product.model or "") or "poe" in head.lower():  # features 'PoE' = camera support only
        return channels(product) or 0
    return 0


def roll_length(product: Product) -> int | None:
    return _number(r"(\d{2,3})\s*м(?:\b|\.|етр)", product.text)


def _pick(catalog, overrides, predicate, sort_key, limit=3):
    rows = [(p, price_of(p, overrides)) for p in catalog.values() if predicate(p)]
    rows = [(p, price) for p, price in rows if price is not None]
    rows.sort(key=lambda pair: sort_key(*pair))
    return rows[:limit]


def build_kit(cameras: int, *, resolution_mp: int | None = None, outdoor: bool = True, cable_m: int | None = None,
              brand: str | None = None, overrides: dict[str, float] | None = None,
              catalog: dict[str, Product] | None = None) -> dict[str, Any]:
    """Candidate components (cheapest suitable first) from the real catalog; the consultant/owner picks."""
    catalog = catalog if catalog is not None else products()
    cameras = max(1, min(int(cameras), 64))
    brand_l = (brand or "").lower()
    res = re.compile(rf"\b{resolution_mp}\s*(?:mp|мп|мп\b|mpx)", re.I) if resolution_mp else None

    analog = re.compile(r"\b(?:ahd|hdcvi|hd-cvi|tvi|cvi|xvr|dvr|аналог)", re.I)
    wireless = re.compile(r"wi-?fi|wifi|4g|акумулятор|battery|sim", re.I)

    def own(p):  # name/model/features only (category names contain generic words)
        return f"{p.name} {p.model} {' '.join(p.features)}".lower()

    def is_camera(p):
        text = own(p)
        return ("камери відеоспостереження" in p.category.lower() and re.search(r"\bip\b|poe", text) is not None
                and not analog.search(text) and not wireless.search(text)
                and (not brand_l or brand_l in p.brand.lower()) and (res is None or bool(res.search(text))))

    def is_nvr(p):
        text = own(p)
        return (("nvr" in text) or ("відеореєстратор" in text and re.search(r"\bip\b", text) is not None)) \
            and not analog.search(text) and not wireless.search(text) and (channels(p) or 0) >= cameras \
            and "ajax" not in p.brand.lower()

    def is_hdd(p):
        text = own(p)
        return re.search(r"жорсткий диск|жесткий диск|\bhdd\b", text) is not None and "реєстратор" not in text


    def is_cable(p):
        text = own(p)
        if "кабельна продукція" not in p.category.lower() or not re.search(r"utp|кпв|квп|кнп|вита пара|cat\.?5", text):
            return False
        return ("зовн" in text or "кнп" in text or "outdoor" in text) if outdoor else True

    meters = int(cable_m) if cable_m else cameras * 25
    components: dict[str, list[dict[str, Any]]] = {}
    poe_first = lambda p, pr: ("poe" not in own(p), pr)  # noqa: E731 - wired PoE cameras for NVR kits
    components["cameras"] = [p.public(price, cameras) for p, price in _pick(catalog, overrides, is_camera, poe_first)]
    # Recorders with enough built-in PoE ports first: then the kit needs no separate PoE switch.
    nvr_rows = _pick(catalog, overrides, is_nvr,
                     lambda p, pr: (nvr_poe_ports(p) < cameras, channels(p) or 0, pr))
    components["nvr"] = []
    for p, price in nvr_rows:
        row = p.public(price, 1)
        row["poe_ports"] = nvr_poe_ports(p)
        row["needs_poe_switch"] = row["poe_ports"] < cameras
        components["nvr"].append(row)
    components["hdd"] = [p.public(price, 1) for p, price in _pick(catalog, overrides, is_hdd, lambda p, pr: pr)]
    main_nvr_poe = components["nvr"][0]["poe_ports"] if components["nvr"] else 0
    switch_needed = main_nvr_poe < cameras
    missing_poe = cameras - main_nvr_poe  # cameras that are not powered by the recorder itself

    def is_switch(p):
        return is_poe_switch(p) and (ports(p) or 0) >= missing_poe

    components["poe_switch"] = ([p.public(price, 1) for p, price in
                                 _pick(catalog, overrides, is_switch, lambda p, pr: (ports(p), pr))]
                                if switch_needed else [])
    cable = []
    for p, price in _pick(catalog, overrides, is_cable, lambda p, pr: pr, limit=6):
        length = roll_length(p)
        if length:
            cable.append(p.public(price, max(1, math.ceil(meters / length))))
        if len(cable) == 3:
            break
    components["cable"] = cable
    notes = [f"Кабель орієнтовно {meters} м ({'зовнішній' if outdoor else 'внутрішній'}); точний метраж — після огляду/плану.",
             "Ємність диска підбирається під потрібний архів; сумісність і наявність перевіряє менеджер.",
             ]
    if switch_needed:
        notes.append(f"PoE-комутатор потрібен: реєстратор живить {main_nvr_poe} з {cameras} камер." if main_nvr_poe
                     else "PoE-комутатор потрібен: реєстратор без вбудованих PoE-портів.")
    else:
        notes.append(f"Окремий PoE-комутатор НЕ потрібен: реєстратор має {main_nvr_poe} вбудованих PoE-портів "
                     f"для {cameras} камер. Не додавай комутатор у кошик.")
    missing = [name for name, rows in components.items() if not rows and (name != "poe_switch" or switch_needed)]
    if missing:
        notes.append("Не знайдено в каталозі: " + ", ".join(missing) + " — підбере менеджер.")
    return {"cameras": cameras, "components": components, "poe_switch_needed": switch_needed, "notes": notes}


def cart_link(items: list[dict[str, Any]], *, origin: str = "https://alt-cam.net.ua",
              overrides: dict[str, float] | None = None, catalog: dict[str, Product] | None = None) -> dict[str, Any]:
    catalog = catalog if catalog is not None else products()
    lines, unknown, parts, total, priced = [], [], [], 0.0, True
    for item in items or []:
        pid = str((item or {}).get("id") or "")
        try:
            qty = max(1, min(int((item or {}).get("qty") or 1), 99))
        except (TypeError, ValueError):
            qty = 1
        product = catalog.get(pid)
        if product is None or not CART_ID.match(pid):
            unknown.append(pid)
            continue
        price = price_of(product, overrides)
        if price is None:
            priced = False
        else:
            total += price * qty
        parts.append(f"{pid}:{qty}")
        lines.append(product.public(price, qty))
    removed = _drop_redundant_switches(catalog, parts)
    if removed:
        keep = [part for part in parts if part.split(":")[0] not in removed]
        lines = [row for row in lines if row["id"] not in removed]
        total = sum((row["price_uah"] or 0) * row["qty"] for row in lines)
        priced = all(row["price_uah"] is not None for row in lines)
        parts = keep
    if not parts:
        return {"ok": False, "error": "no_valid_items", "unknown_ids": unknown}
    return {"ok": True, "url": f"{origin.rstrip('/')}/catalog.html?cart={quote(','.join(parts), safe=':,')}",
            "items": lines, "total_uah": round(total, 2) if priced else None, "unknown_ids": unknown,
            "removed_redundant_poe_switch": removed,
            "note": "Ціни за каталогом сайту; наявність і остаточну суму підтверджує менеджер."
                    + (" PoE-комутатор прибрано: реєстратор сам живить усі камери." if removed else "")}


def _drop_redundant_switches(catalog: dict[str, Product], parts: list[str]) -> list[str]:
    """Ids of PoE switches that are redundant because the recorder in the same cart powers every camera."""
    qty = {}
    for part in parts:
        pid, _, count = part.partition(":")
        qty[pid] = qty.get(pid, 0) + int(count or 1)
    items = [(catalog[pid], count) for pid, count in qty.items() if pid in catalog]
    cams = sum(count for p, count in items if "камери відеоспостереження" in p.category.lower() and not is_recorder(p))
    nvr_poe = sum(nvr_poe_ports(p) * count for p, count in items if is_recorder(p))
    switches = [p.id for p, _ in items if is_poe_switch(p)]
    if not switches or not cams or nvr_poe < cams:
        return []
    return switches
