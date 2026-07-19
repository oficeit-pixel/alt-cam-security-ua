from __future__ import annotations

import json
import re
import textwrap
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "social-posts" / "instagram-catalog"
CARDS = OUT / "product-cards"
PHOTOS = OUT / "product-photos"

CATEGORIES = [
    ("cameras", "КАМЕРИ", "https://viatec.ua/ru/catalog/cameras", "#ffd400"),
    ("recorders", "РЕЄСТРАТОРИ", "https://viatec.ua/ru/catalog/dvr", "#ffd400"),
    ("intercoms", "ДОМОФОНИ", "https://viatec.ua/ru/catalog/vth", "#21c4f3"),
    (
        "ajax",
        "AJAX",
        "https://viatec.ua/ru/catalog/alarm-ppk/proizvoditel%3A390",
        "#5cf2b0",
    ),
    (
        "backup",
        "РЕЗЕРВ",
        "https://viatec.ua/ru/catalog/istochniki-bespereboinogo-pitania-12-24v",
        "#ffe35a",
    ),
]

UA_REPLACEMENTS = {
    "видеокамера": "відеокамера",
    "Видеокамера": "Відеокамера",
    "Видеорегистратор": "Відеореєстратор",
    "видеорегистратор": "відеореєстратор",
    "канальный": "канальний",
    "дюймов": "дюймів",
    "беспроводной": "бездротовий",
    "охранной": "охоронної",
    "Охранная": "Охоронна",
    "охранная": "охоронна",
    "централь": "централь",
    "сигнализации": "сигналізації",
    "движения": "руху",
    "Источник": "Джерело",
    "источник": "джерело",
    "бесперебойного": "безперебійного",
    "питания": "живлення",
}


def fetch(url: str) -> bytes:
    url = urllib.parse.urljoin("https://viatec.ua", url)
    parts = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, urllib.parse.quote(urllib.parse.unquote(parts.path)), parts.query, parts.fragment)
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read()


def catalog_products(url: str) -> list[dict]:
    html = fetch(url).decode("utf-8", errors="replace")
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    )
    for raw in scripts:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        entity = payload.get("mainEntity")
        if isinstance(entity, dict) and entity.get("@type") == "OfferCatalog":
            items = entity.get("itemListElement", [])
            return [item for item in items if isinstance(item, dict)]
    raise RuntimeError(f"OfferCatalog not found: {url}")


def normalized_product(item: dict) -> dict | None:
    offer = item.get("offers") or {}
    price = offer.get("price")
    image = item.get("image")
    url = item.get("@id")
    name = item.get("name")
    availability = str(offer.get("availability", ""))
    try:
        price = int(round(float(price)))
    except (TypeError, ValueError):
        return None
    if not all((name, image, url)) or price <= 0 or "InStock" not in availability:
        return None
    return {
        "name": str(name).strip(),
        "price": price,
        "image": urllib.parse.urljoin("https://viatec.ua", str(image)),
        "url": str(url),
        "sku": str(offer.get("sku", "")),
        "price_valid_until": str(offer.get("priceValidUntil", "")),
    }


def choose_balanced(items: list[dict]) -> list[dict]:
    products = [p for item in items if (p := normalized_product(item))]
    products.sort(key=lambda product: product["price"])
    if len(products) < 10:
        raise RuntimeError(f"Only {len(products)} in-stock priced products found")
    budget = products[:5]
    premium = products[-5:]
    selected: list[dict] = []
    for low, high in zip(budget, premium):
        low = dict(low)
        high = dict(high)
        low["tier"] = "БЮДЖЕТ"
        high["tier"] = "РОЗШИРЕНИЙ"
        selected.extend((low, high))
    return selected


def ua_name(value: str) -> str:
    for source, target in UA_REPLACEMENTS.items():
        value = value.replace(source, target)
    return value


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def fit_photo(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    image = image.convert("RGBA")
    bg = Image.new("RGBA", box, (247, 247, 247, 255))
    contained = ImageOps.contain(image, (box[0] - 80, box[1] - 80), Image.Resampling.LANCZOS)
    x = (box[0] - contained.width) // 2
    y = (box[1] - contained.height) // 2
    bg.alpha_composite(contained, (x, y))
    return bg.convert("RGB")


def wrapped(draw: ImageDraw.ImageDraw, text: str, box_width: int, fnt, max_lines=4):
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= box_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = textwrap.shorten(lines[-1], width=max(8, len(lines[-1]) - 2), placeholder="…")
    return lines


def render_card(product: dict, category: str, accent: str, index: int, photo_path: Path):
    w, h = 1080, 1920
    canvas = Image.new("RGB", (w, h), "#090a0d")
    draw = ImageDraw.Draw(canvas)
    accent_rgb = tuple(int(accent[i : i + 2], 16) for i in (1, 3, 5))
    draw.rectangle((0, 0, w, 18), fill=accent_rgb)
    draw.rounded_rectangle((54, 58, 1026, 174), 28, outline="#ffffff", width=2)
    draw.text((84, 83), "ALT-CAM SECURITY UA", font=font(35, True), fill="white")
    draw.text((720, 91), category, font=font(25, True), fill=accent_rgb, anchor="ra")

    photo = fit_photo(Image.open(photo_path), (972, 720))
    canvas.paste(photo, (54, 220))
    draw.rounded_rectangle((54, 220, 1026, 940), 30, outline=accent_rgb, width=5)

    tier = product["tier"]
    badge_w = 320 if tier == "РОЗШИРЕНИЙ" else 245
    draw.rounded_rectangle((72, 972, 72 + badge_w, 1042), 24, fill=accent_rgb)
    draw.text((94, 990), tier, font=font(30, True), fill="#090a0d")

    name = ua_name(product["name"])
    name_font = font(48, True)
    lines = wrapped(draw, name, 920, name_font, max_lines=4)
    y = 1080
    for line in lines:
        draw.text((72, y), line, font=name_font, fill="white")
        y += 60

    price = f"{product['price']:,}".replace(",", " ")
    draw.rounded_rectangle((72, 1360, 590, 1460), 25, outline=accent_rgb, width=4)
    draw.text((102, 1383), f"{price} грн", font=font(48, True), fill=accent_rgb)

    draw.text((72, 1515), "• Перевірене обладнання ALT-CAM", font=font(31), fill="#e7e7e7")
    draw.text((72, 1570), "• Підбір під ваш об'єкт і бюджет", font=font(31), fill="#e7e7e7")
    draw.text((72, 1625), "• Монтаж, налаштування та сервіс", font=font(31), fill="#e7e7e7")

    draw.line((72, 1735, 1008, 1735), fill=accent_rgb, width=3)
    draw.text((72, 1770), "Напишіть «ПІДБІР» у Direct", font=font(38, True), fill="white")
    draw.text((72, 1830), "Київ • Вишгород • Київська область", font=font(26), fill="#c9c9c9")
    draw.text((1008, 1830), f"{index:02d}/10", font=font(26, True), fill=accent_rgb, anchor="ra")
    return canvas


def main():
    CARDS.mkdir(parents=True, exist_ok=True)
    PHOTOS.mkdir(parents=True, exist_ok=True)
    catalog: dict = {
        "generated_on": date.today().isoformat(),
        "source": "https://viatec.ua/ru",
        "categories": [],
    }
    for slug, title, url, accent in CATEGORIES:
        selected = choose_balanced(catalog_products(url))
        category_dir = CARDS / slug
        photo_dir = PHOTOS / slug
        category_dir.mkdir(parents=True, exist_ok=True)
        photo_dir.mkdir(parents=True, exist_ok=True)
        for index, product in enumerate(selected, start=1):
            suffix = Path(urllib.parse.urlparse(product["image"]).path).suffix or ".webp"
            photo_path = photo_dir / f"{index:02d}{suffix}"
            photo_path.write_bytes(fetch(product["image"]))
            card = render_card(product, title, accent, index, photo_path)
            tier_slug = "budget" if product["tier"] == "БЮДЖЕТ" else "premium"
            card_path = category_dir / f"{index:02d}-{tier_slug}.jpg"
            card.save(card_path, quality=94, optimize=True)
            product["card_path"] = str(card_path.relative_to(ROOT)).replace("\\", "/")
            product["photo_path"] = str(photo_path.relative_to(ROOT)).replace("\\", "/")
        catalog["categories"].append(
            {"slug": slug, "title": title, "source_url": url, "products": selected}
        )
    (OUT / "products.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Created {sum(len(c['products']) for c in catalog['categories'])} cards")


if __name__ == "__main__":
    main()
