from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week"
PROMPTS_DIR = OUT_DIR / "image-prompts"
MEDIA_DIR = OUT_DIR / "media"
CALENDAR_DIR = ROOT / "social-posts" / "calendar"
DATA_PATH = CALENDAR_DIR / "product-week-data.js"
HTML_PATH = CALENDAR_DIR / "product-week.html"
PUBLISHING_PATH = OUT_DIR / "publishing-posts.json"

SITE = "https://alt-cam.net.ua"
BOT = "https://t.me/alt_cam_bot"
LOCATION = "Київ • Вишгород • Київська область"
HASHTAGS_BASE = "#AltCam #відеоспостереження #системибезпеки #монтажкамер #домофон #Ajax #Київ #Вишгород"

ANTHRACITE = "#121212"
PANEL = "#1B1B1F"
GRAPHITE = "#2C2C31"
YELLOW = "#FFCC00"
WHITE = "#F5F5F7"
MUTED = "#86868B"
LINE = "#3A3A42"


PRODUCTS = [
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "Відеоспостереження",
        "product": "Hikvision DS-2CD2443G2-I Black 4МП",
        "price": "орієнтир постачальника: 6 233 ₴",
        "audience": "квартира / офіс",
        "keyword": "КАМЕРА",
        "hook": "Камера в приміщенні, яка не виглядає як “офісний монстр”.",
        "benefits": ["4МП деталізація", "компактний корпус", "підходить для офісу й квартири", "легко інтегрувати в готову систему"],
    },
    {
        "source": "NeoLight",
        "source_url": "https://neolight.in.ua/uk",
        "category": "Домофонія",
        "product": "NeoLight OPTIMA GSM",
        "price": "орієнтир постачальника: 7 650 ₴",
        "audience": "ворота / приватний будинок",
        "keyword": "ДОМОФОН",
        "hook": "Виклик на ворота без зайвих дротів там, де класичний домофон незручний.",
        "benefits": ["GSM-сценарій", "панель виклику", "актуально для воріт", "зручно для приватного будинку"],
    },
    {
        "source": "ЮГТОРГ / BigOpt",
        "source_url": "https://yugtorg.bigopt.com/",
        "category": "Кабель / монтаж",
        "product": "Одескабель КППт-ВП U/UTP Cat.5E CU 305 м для зовнішніх робіт",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "монтаж камер зовні",
        "keyword": "КАБЕЛЬ",
        "hook": "Поганий кабель може зіпсувати навіть хорошу камеру.",
        "benefits": ["мідний кабель CU", "для зовнішніх робіт", "305 м у бухті", "основа стабільної системи"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru/product/DHI-VTH2421FW-P",
        "category": "Домофонія",
        "product": "Dahua DHI-VTH2421FW-P 7” PoE",
        "price": "орієнтир постачальника: 6 480 ₴",
        "audience": "квартира / офіс / будинок",
        "keyword": "ДОМОФОН",
        "hook": "Відеодомофон, який може бути центром контролю входу.",
        "benefits": ["7” TFT", "PoE", "підключення камер Dahua/ONVIF", "запис дзвінка на карту пам’яті"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "Відеоспостереження",
        "product": "Hikvision DS-2CD1047G3H-LIUF 4МП",
        "price": "орієнтир постачальника: 7 704 ₴",
        "audience": "двір / фасад / вхід",
        "keyword": "КАМЕРА",
        "hook": "Коли треба бачити не просто силует, а реальну картинку біля входу.",
        "benefits": ["4МП", "вуличний формат", "підходить для входу й двору", "сильний акцент у рекламній картці"],
    },
    {
        "source": "NeoLight",
        "source_url": "https://neolight.in.ua/uk",
        "category": "Домофонія",
        "product": "NeoLight NeoKit HD WF + замок",
        "price": "орієнтир постачальника: 10 770 ₴",
        "audience": "будинок / офіс / хвіртка",
        "keyword": "ДОМОФОН",
        "hook": "Не просто бачити гостя — а відкривати там, де це безпечно.",
        "benefits": ["Wi‑Fi комплект", "панель + монітор", "замок у сценарії", "керування входом"],
    },
    {
        "source": "ЮГТОРГ / BigOpt",
        "source_url": "https://yugtorg.bigopt.com/goods-price/4/",
        "category": "Wi‑Fi відеоспостереження",
        "product": "YOSO YO-IPC43D5MP50 PTZ 5МП Wi‑Fi з сиреною",
        "price": "орієнтир постачальника: 2 398,50 ₴",
        "audience": "дача / двір / тимчасовий об’єкт",
        "keyword": "КАМЕРА",
        "hook": "Камера для об’єкта, де немає бажання тягнути повну систему одразу.",
        "benefits": ["5МП", "Wi‑Fi", "PTZ", "сирена та SD-карта"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "Відеоспостереження",
        "product": "Dahua DH-HAC-HFW1801TLMP-IL-A 8МП",
        "price": "орієнтир постачальника: 2 970 ₴",
        "audience": "магазин / склад / двір",
        "keyword": "КАМЕРА",
        "hook": "8МП — це не магія. Але для правильного місця це сильний аргумент.",
        "benefits": ["8МП", "HDCVI", "вуличний форм-фактор", "вигідна точка входу"],
    },
    {
        "source": "NeoLight",
        "source_url": "https://neolight.in.ua/uk",
        "category": "Домофонія",
        "product": "NeoLight MEZZO Hybrid HD KIT Graphite 10.1” Wi‑Fi",
        "price": "орієнтир постачальника: 16 120 ₴",
        "audience": "преміальний будинок / офіс",
        "keyword": "ДОМОФОН",
        "hook": "Коли домофон має виглядати як частина інтер’єру, а не компроміс.",
        "benefits": ["10.1” монітор", "Wi‑Fi", "гібридний комплект", "2Мп відеопанель"],
    },
    {
        "source": "ЮГТОРГ / BigOpt",
        "source_url": "https://yugtorg.bigopt.com/",
        "category": "Серверна / монтаж",
        "product": "Шафа Merlion 15U 600×600×768 мм",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "офіс / склад / бізнес",
        "keyword": "ЩИТ",
        "hook": "Коли кабелі заховані правильно — систему не страшно обслуговувати.",
        "benefits": ["15U", "скляні двері", "замок", "порядок для NVR/PoE/UPS"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "Контроль доступу",
        "product": "Dahua DHI-ASR2100A-D Marine IP66",
        "price": "орієнтир постачальника: 1 215 ₴",
        "audience": "офіс / склад / вхідна зона",
        "keyword": "ДОСТУП",
        "hook": "Доступ має відкриватися своїм — і закриватися для випадкових.",
        "benefits": ["IP66", "зчитувач", "для контролю доступу", "підходить для суворіших умов"],
    },
    {
        "source": "NeoLight",
        "source_url": "https://neolight.in.ua/uk",
        "category": "Домофонія + відео",
        "product": "NeoLight ALPHA Hybrid HD KIT Graphite + 2 IP камери",
        "price": "орієнтир постачальника: 16 220 ₴",
        "audience": "будинок / офіс / вхідна група",
        "keyword": "ДОМОФОН",
        "hook": "Вхід і відеонагляд в одному сценарії — без зоопарку пристроїв.",
        "benefits": ["гібридний домофон", "2 IP камери", "комплектне рішення", "зручно для контролю входу"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "Домофонія",
        "product": "Hikvision DS-KH6110-WE1/White 4.3”",
        "price": "орієнтир постачальника: 4 050 ₴",
        "audience": "квартира / орендна нерухомість",
        "keyword": "ДОМОФОН",
        "hook": "Маленький монітор, який закриває базову задачу контролю входу.",
        "benefits": ["4.3”", "білий корпус", "для базового сценарію", "підходить для квартири"],
    },
    {
        "source": "ЮГТОРГ / BigOpt",
        "source_url": "https://yugtorg.bigopt.com/",
        "category": "Кабель / монтаж",
        "product": "Ritar FTP Cat.6 CU 305 м",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "IP-камери / мережа / PoE",
        "keyword": "КАБЕЛЬ",
        "hook": "IP-камера починається не з камери. Вона починається з нормальної лінії.",
        "benefits": ["Cat.6", "CU", "FTP", "для стабільної мережі"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "Відеоспостереження",
        "product": "Dahua WizMind Triple-Sight DH-IPC-MFW5241T2-E3-ASE",
        "price": "орієнтир постачальника: 17 550 ₴",
        "audience": "склад / периметр / бізнес",
        "keyword": "КАМЕРА",
        "hook": "Одна точка — три погляди. Для об’єктів, де сліпі зони коштують дорого.",
        "benefits": ["3×2МП", "Triple-Sight", "різні фокусні відстані", "для складних зон"],
    },
    {
        "source": "NeoLight",
        "source_url": "https://neolight.in.ua/uk",
        "category": "Домофонія",
        "product": "NeoLight NeoKIT FHD PRO + замок",
        "price": "орієнтир постачальника: 9 059 ₴",
        "audience": "хвіртка / двері / офіс",
        "keyword": "ДОМОФОН",
        "hook": "Відеодомофон без замка — це половина контролю.",
        "benefits": ["FHD PRO", "комплект із замком", "для дверей/хвіртки", "зручний сценарій входу"],
    },
    {
        "source": "ЮГТОРГ / BigOpt",
        "source_url": "https://yugtorg.bigopt.com/",
        "category": "Резервне живлення",
        "product": "BMS JK-BD6A24S20P Li-Ion/LiFePO4/LTO",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "резерв для мережі / безпеки",
        "keyword": "РЕЗЕРВ",
        "hook": "Резерв живлення — це не просто акумулятор. Це контроль і захист.",
        "benefits": ["Li‑Ion/LiFePO4/LTO", "до 24S", "200A", "CAN/RS485/Bluetooth"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru",
        "category": "PTZ відеоспостереження",
        "product": "Hikvision DS-2DE1C200IW-DE3(F1)(S7) 2МП PTZ",
        "price": "орієнтир постачальника: 5 063 ₴",
        "audience": "двір / парковка / магазин",
        "keyword": "КАМЕРА",
        "hook": "Коли треба не тільки бачити, а й змінювати напрям огляду.",
        "benefits": ["PTZ", "2МП", "4 мм", "для гнучкого огляду"],
    },
    {
        "source": "NeoLight",
        "source_url": "https://neolight.in.ua/uk",
        "category": "Домофонія",
        "product": "NeoLight ALPHA Hybrid HD KIT Graphite + 2Мп камера",
        "price": "орієнтир постачальника: 12 490 ₴",
        "audience": "будинок / квартира / офіс",
        "keyword": "ДОМОФОН",
        "hook": "Готовий комплект, щоб не збирати домофон “по шматках”.",
        "benefits": ["гібридний комплект", "2Мп камера", "graphite дизайн", "готовий сценарій входу"],
    },
    {
        "source": "ЮГТОРГ / BigOpt",
        "source_url": "https://bigopt.com/bnc.htm",
        "category": "Кабель / аксесуари",
        "product": "Патчкорд BNC + DC 25 м",
        "price": "орієнтир постачальника: 304,20 ₴",
        "audience": "аналогові / HDCVI камери",
        "keyword": "КАБЕЛЬ",
        "hook": "Іноді слабке місце системи — не камера, а кабель між камерою і реєстратором.",
        "benefits": ["BNC + DC", "25 м", "відео + живлення", "для швидкого монтажу"],
    },
    {
        "source": "VIATEC",
        "source_url": "https://viatec.ua/ru/product/DHI-VTH2421FW-P",
        "category": "Домофонія",
        "product": "Dahua DHI-VTH2421FB-P",
        "price": "орієнтир постачальника: 6 750 ₴",
        "audience": "квартира / офіс / ресепшн",
        "keyword": "ДОМОФОН",
        "hook": "Контроль входу має бути простим для власника і зрозумілим для гостя.",
        "benefits": ["відеомонітор", "сценарій входу", "Dahua екосистема", "для квартири й офісу"],
    },
]


def slugify(text: str) -> str:
    mapping = {
        "КАМЕРА": "camera",
        "ДОМОФОН": "intercom",
        "КАБЕЛЬ": "cable",
        "ЩИТ": "rack",
        "ДОСТУП": "access",
        "РЕЗЕРВ": "backup",
    }
    return mapping.get(text, "product")


def public_product(product: dict) -> dict:
    return {
        "category": product["category"],
        "product": product["product"],
        "price": clean_price(product["price"]),
        "audience": product["audience"],
        "keyword": product["keyword"],
        "hook": product["hook"],
        "benefits": product["benefits"],
    }


def clean_price(value: str) -> str:
    return value.replace("орієнтир постачальника:", "орієнтир:").strip()


def price_line(product: dict) -> str:
    if clean_price(product["price"]).lower().startswith("ціну"):
        return "Вартість підбираємо під об’єкт, комплектацію та монтаж. Перед публікацією можемо додати точну ціну."
    return f"Ціна: {clean_price(product['price'])}. Перед публікацією фінальну ціну підтверджуємо по наявності та комплектації."


def hashtags(product: dict) -> str:
    extra = {
        "Відеоспостереження": "#камери #відеонагляд #Hikvision #Dahua",
        "Домофонія": "#домофон #відеодомофон #NeoLight #Dahua",
        "Контроль доступу": "#контрольдоступу #СКУД #Dahua",
        "Кабель / монтаж": "#кабель #монтаж #PoE #UTP",
        "Резервне живлення": "#резервнеживлення #UPS #LiFePO4",
    }
    return f"{HASHTAGS_BASE} {extra.get(product['category'], '')}".strip()


def product_caption(product: dict, platform: str) -> str:
    title = product["hook"]
    bullets = "\n".join(f"• {item}" for item in product["benefits"])
    if platform == "facebook":
        return (
            f"{title}\n\n"
            f"Товар: {product['product']}\n"
            f"Категорія: {product['category']}\n\n"
            f"Кому підійде: {product['audience']}.\n\n"
            f"Що важливо:\n{bullets}\n\n"
            f"{price_line(product)}\n\n"
            f"Хочете підібрати без помилки? Напишіть «{product['keyword']}» у Telegram або відкрийте сайт.\n"
            f"🤖 {BOT}\n🌐 {SITE}\n📍 {LOCATION}\n\n{hashtags(product)}"
        )
    if platform == "instagram":
        return (
            f"{title}\n\n"
            f"{product['product']} — варіант для: {product['audience']}.\n\n"
            f"{bullets}\n\n"
            f"Напишіть «{product['keyword']}» — підкажемо, чи підходить саме під ваш об’єкт.\n"
            f"🤖 {BOT}\n🌐 {SITE}\n\n{hashtags(product)}"
        )
    if platform == "threads":
        return (
            f"{title}\n\n"
            f"Питання до власників: ви обираєте {product['category'].lower()} за ціною чи за сценарієм об’єкта?\n\n"
            f"Ми за другий варіант: спочатку задача, потім модель.\n"
            f"Напишіть «{product['keyword']}» — підкажемо коротко."
        )
    if platform == "telegram":
        return (
            f"<b>{title}</b>\n\n"
            f"<b>Товар:</b> {product['product']}\n"
            f"<b>Для кого:</b> {product['audience']}\n\n"
            f"{bullets}\n\n"
            f"<code>{price_line(product)}</code>\n\n"
            f"Натисніть кнопку або напишіть «{product['keyword']}» — підберемо варіант під об’єкт.\n"
            f"{BOT}"
        )
    if platform == "youtube":
        return (
            f"Community post: {title}\n\n"
            f"Показуємо {product['product']} і пояснюємо, де воно доречне: {product['audience']}.\n"
            f"Якщо хочете розбір у відео — напишіть у коментарі «{product['keyword']}»."
        )
    return title


def image_prompt(product: dict, post_type: str) -> str:
    category_direction = {
        "Відеоспостереження": "steel-blue secondary glow, field-of-view lines, modern home/business architecture, precision optics",
        "PTZ відеоспостереження": "steel-blue secondary glow, PTZ camera as hero, parking or yard, direction arrows, intelligent surveillance",
        "Wi‑Fi відеоспостереження": "home yard or temporary site, Wi-Fi signal lines, clean product card, no cheap marketplace look",
        "Домофонія": "warm white/champagne glow, premium entrance door, gate, smart residential access",
        "Домофонія + відео": "premium entrance with intercom monitor and camera ecosystem, warm residential lighting",
        "Контроль доступу": "cyan metallic ambient, office glass doors, RFID access zone, professional identification",
        "Кабель / монтаж": "blue-grey infrastructure mood, cable texture, connectors, neat technical graphite background",
        "Кабель / аксесуари": "clean accessory catalog presentation, cable and connectors detailed, graphite platform",
        "Серверна / монтаж": "server rack, NVR, PoE switch, UPS, labeled cables, clean engineering infrastructure",
        "Резервне живлення": "amber electric glow, battery management, backup power, technical cabinet, stable energy",
    }.get(product["category"], "premium security-tech product card")
    hero = "product-only premium catalog card" if post_type == "product" else "product plus ALT-CAM installer/expert"
    return f"""Use case: ads-marketing
Asset type: social product card / carousel slide
Primary request: create a premium commercial product card for ALT-CAM Security UA in the same style as the user's reference examples.
Product: {product['product']}
Category: {product['category']}
Main visual mode: {hero}
Scene/backdrop: {category_direction}
Composition: 1:1 square, deep anthracite #121212 background, graphite panels #1B1B1F/#2C2C31, product occupies 50–65% of composition, realistic commercial product photography, subtle glassmorphism, Apple/premium smart-home mood, controlled cinematic lighting, ALT-CAM yellow #FFCC00 only as accent lines, small labels and CTA zones.
Text zones: leave clean space for headline “{product['hook']}”, short feature line, and bottom CTA “НАПИШІТЬ «{product['keyword']}»”.
Brand zone: bottom branded ALT-CAM Security UA area, professional European security integrator feeling.
Strict product preservation: if a product photo is uploaded, preserve exact body shape, ports, lens quantity, brackets, sensors, buttons, color and manufacturer logo. Do not redesign the equipment.
Avoid: cheap marketplace style, red SALE stickers, cartoon icons, military/police mood, random unreadable text, full yellow background, fake functions.
"""


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_logo(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> None:
    s = scale
    size = int(64 * s)
    draw.rounded_rectangle((x, y, x + size, y + size), radius=int(16 * s), fill=YELLOW)
    draw.rounded_rectangle((x + int(16 * s), y + int(22 * s), x + int(50 * s), y + int(45 * s)), radius=int(7 * s), fill=ANTHRACITE)
    draw.ellipse((x + int(25 * s), y + int(27 * s), x + int(43 * s), y + int(45 * s)), fill=YELLOW)
    draw.ellipse((x + int(31 * s), y + int(32 * s), x + int(38 * s), y + int(39 * s)), fill=ANTHRACITE)
    draw.text((x + int(78 * s), y - int(2 * s)), "ALT-CAM", fill=WHITE, font=font(int(40 * s), True))
    draw.text((x + int(82 * s), y + int(40 * s)), "SECURITY UA", fill=YELLOW, font=font(int(18 * s), True))


def category_accent(product: dict) -> str:
    if "Домофон" in product["category"]:
        return "#F6D58B"
    if "доступ" in product["category"].lower():
        return "#66D9EF"
    if "Кабель" in product["category"]:
        return "#8EA7C2"
    if "Резерв" in product["category"]:
        return "#FFB24A"
    if "Сервер" in product["category"]:
        return "#A8ADB7"
    return "#66AFFF"


def short_category(product: dict) -> str:
    category = product["category"]
    if "Відеоспостереження" in category or "відеоспостереження" in category:
        return "ВІДЕОНАГЛЯД"
    if "Домофон" in category:
        return "ДОМОФОНІЯ"
    if "Кабель" in category:
        return "КАБЕЛЬ"
    if "Резерв" in category:
        return "РЕЗЕРВ"
    if "Контроль" in category:
        return "СКУД"
    if "Сервер" in category:
        return "СЕРВЕРНА"
    return category[:16].upper()


def draw_product_symbol(draw: ImageDraw.ImageDraw, product: dict, x: int, y: int, w: int, h: int, accent: str) -> None:
    keyword = product["keyword"]
    if keyword == "ДОМОФОН":
        draw.rounded_rectangle((x + w * 0.15, y + h * 0.10, x + w * 0.72, y + h * 0.70), radius=32, fill="#E9E9EE", outline=accent, width=4)
        draw.rectangle((x + w * 0.22, y + h * 0.20, x + w * 0.65, y + h * 0.48), fill="#111114")
        draw.ellipse((x + w * 0.38, y + h * 0.27, x + w * 0.50, y + h * 0.39), fill=accent)
        draw.rounded_rectangle((x + w * 0.77, y + h * 0.15, x + w * 0.94, y + h * 0.78), radius=28, fill="#151519", outline=accent, width=3)
        draw.ellipse((x + w * 0.82, y + h * 0.22, x + w * 0.89, y + h * 0.29), fill="#050506", outline=accent, width=2)
        draw.rounded_rectangle((x + w * 0.82, y + h * 0.55, x + w * 0.89, y + h * 0.64), radius=12, fill=accent)
    elif keyword in {"КАМЕРА"}:
        draw.rounded_rectangle((x + w * 0.08, y + h * 0.23, x + w * 0.72, y + h * 0.55), radius=34, fill="#F2F2F5", outline="#FFFFFF", width=3)
        draw.rectangle((x + w * 0.68, y + h * 0.34, x + w * 0.95, y + h * 0.43), fill="#F2F2F5")
        draw.ellipse((x + w * 0.18, y + h * 0.27, x + w * 0.46, y + h * 0.55), fill="#050506", outline=accent, width=10)
        draw.ellipse((x + w * 0.26, y + h * 0.35, x + w * 0.38, y + h * 0.47), fill="#2C2C31", outline="#777", width=3)
        draw.ellipse((x + w * 0.31, y + h * 0.39, x + w * 0.35, y + h * 0.43), fill="#FFFFFF")
        draw.rounded_rectangle((x + w * 0.56, y + h * 0.58, x + w * 0.88, y + h * 0.72), radius=16, fill=YELLOW)
        draw.text((x + w * 0.60, y + h * 0.61), "ALT-CAM", fill=ANTHRACITE, font=font(24, True))
    elif keyword in {"КАБЕЛЬ"}:
        for i, color in enumerate([accent, YELLOW, "#D6D6DB", "#6B7280"]):
            yy = y + int(h * (0.18 + i * 0.13))
            draw.arc((x + w * 0.10, yy, x + w * 0.90, yy + h * 0.55), 200, 340, fill=color, width=18)
        draw.rounded_rectangle((x + w * 0.62, y + h * 0.35, x + w * 0.94, y + h * 0.55), radius=18, fill="#EDEDF0", outline=accent, width=3)
        draw.rectangle((x + w * 0.91, y + h * 0.39, x + w * 0.98, y + h * 0.51), fill=accent)
    elif keyword == "ЩИТ":
        draw.rounded_rectangle((x + w * 0.20, y + h * 0.08, x + w * 0.78, y + h * 0.86), radius=28, fill="#222229", outline=accent, width=4)
        for i in range(8):
            yy = y + int(h * (0.18 + i * 0.075))
            draw.rectangle((x + w * 0.28, yy, x + w * 0.70, yy + 18), fill="#101014", outline=YELLOW if i % 3 == 0 else "#555", width=2)
        for i, color in enumerate([YELLOW, accent, "#47D18C"]):
            draw.arc((x + w * 0.66 + i * 12, y + h * 0.25, x + w * 0.92 + i * 12, y + h * 0.76), 190, 330, fill=color, width=6)
    elif keyword == "РЕЗЕРВ":
        draw.rounded_rectangle((x + w * 0.22, y + h * 0.18, x + w * 0.78, y + h * 0.72), radius=34, fill="#202026", outline=accent, width=4)
        draw.rectangle((x + w * 0.42, y + h * 0.10, x + w * 0.58, y + h * 0.18), fill=accent)
        draw.rectangle((x + w * 0.32, y + h * 0.36, x + w * 0.68, y + h * 0.53), fill=YELLOW)
        draw.text((x + w * 0.38, y + h * 0.39), "UPS", fill=ANTHRACITE, font=font(34, True))
    else:
        draw.rounded_rectangle((x + w * 0.25, y + h * 0.18, x + w * 0.75, y + h * 0.74), radius=30, fill="#EDEDF0", outline=accent, width=4)
        draw.ellipse((x + w * 0.38, y + h * 0.30, x + w * 0.62, y + h * 0.54), fill="#111114", outline=accent, width=6)


def draw_product_card(post: dict, out: Path) -> None:
    product = post["product"]
    accent = category_accent(product)
    w = h = 1080
    img = Image.new("RGB", (w, h), ANTHRACITE)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((36, 36, w - 36, h - 36), radius=42, fill=PANEL, outline=accent, width=3)
    for i in range(-200, w, 90):
        draw.line((i, 0, i + 360, h), fill="#18181D", width=3)
    draw_logo(draw, 72, 70, 1.0)
    draw.rounded_rectangle((770, 78, 1006, 130), radius=18, fill=accent)
    draw.text((792, 91), short_category(product), fill=ANTHRACITE, font=font(21, True))
    draw_product_symbol(draw, product, 515, 190, 470, 385, accent)
    title_font = font(58, True)
    y = 190
    for line in wrap(draw, post["title"], title_font, 475)[:4]:
        draw.text((72, y + 5), line, fill="#000", font=title_font)
        draw.text((72, y), line, fill=WHITE, font=title_font)
        y += 66
    draw.rectangle((72, y + 18, 460, y + 30), fill=YELLOW)
    y += 78
    draw.text((72, y), product["product"][:42], fill=WHITE, font=font(28, True))
    draw.text((72, y + 42), product["audience"], fill=MUTED, font=font(25))
    info_y = 610
    draw.rounded_rectangle((72, info_y, 1008, info_y + 238), radius=24, fill=GRAPHITE, outline=LINE, width=2)
    draw.text((104, info_y + 28), "ЩО ВАЖЛИВО:", fill=YELLOW, font=font(28, True))
    bx = 104
    by = info_y + 76
    for benefit in product["benefits"][:4]:
        draw.text((bx, by), f"• {benefit}", fill=WHITE, font=font(24))
        by += 31
    price = clean_price(product["price"])
    draw.text((104, info_y + 202), price[:62], fill=MUTED, font=font(21))
    draw.rounded_rectangle((72, 875, 1008, 990), radius=28, fill=YELLOW)
    draw.text((132, 905), f"НАПИШІТЬ «{product['keyword']}»", fill=ANTHRACITE, font=font(40, True))
    draw.text((132, 953), "підберемо варіант під ваш об’єкт", fill=ANTHRACITE, font=font(24))
    draw.text((74, 1016), "alt-cam.net.ua • t.me/alt_cam_bot • Київ / Вишгород", fill=MUTED, font=font(22))
    img.save(out, quality=94)


def draw_reel_cover(post: dict, out: Path) -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), ANTHRACITE)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((44, 44, w - 44, h - 44), radius=48, fill=PANEL, outline=YELLOW, width=4)
    for i in range(-200, w, 120):
        draw.line((i, 0, i + 620, h), fill="#18181D", width=4)
    draw_logo(draw, 84, 96, 1.15)
    draw.rounded_rectangle((84, 235, 430, 295), radius=20, fill=YELLOW)
    draw.text((110, 249), "REELS / SHORTS", fill=ANTHRACITE, font=font(28, True))
    y = 390
    title_font = font(74, True)
    for line in wrap(draw, post["title"], title_font, 880)[:5]:
        draw.text((84, y + 6), line, fill="#000", font=title_font)
        draw.text((84, y), line, fill=WHITE, font=title_font)
        y += 86
    draw.rectangle((84, y + 22, 720, y + 38), fill=YELLOW)
    y += 120
    for idx, slide in enumerate(post["carousel_slides"][1:4], start=1):
        card_y = y + (idx - 1) * 185
        draw.rounded_rectangle((84, card_y, 996, card_y + 148), radius=24, fill=GRAPHITE, outline=LINE, width=2)
        draw.rounded_rectangle((112, card_y + 28, 174, card_y + 90), radius=18, fill=YELLOW)
        draw.text((132, card_y + 38), str(idx), fill=ANTHRACITE, font=font(30, True))
        for line in wrap(draw, slide.replace(f"Слайд {idx + 1}: ", ""), font(30, True), 720)[:2]:
            draw.text((205, card_y + 32), line, fill=WHITE, font=font(30, True))
            card_y += 36
    draw.rounded_rectangle((84, 1575, 996, 1710), radius=30, fill=YELLOW)
    draw.text((135, 1612), "НАПИШІТЬ «ПІДБІР»", fill=ANTHRACITE, font=font(46, True))
    draw.text((135, 1665), "отримаєте рішення під свій об’єкт", fill=ANTHRACITE, font=font(26))
    draw.text((92, 1788), "ALT-CAM Security UA • alt-cam.net.ua • Telegram", fill=MUTED, font=font(25))
    img.save(out, quality=94)


def build_post(product: dict, current_date: date, time_value: time, index: int) -> dict:
    post_id = f"altcam-product-{current_date.isoformat()}-{index:02d}-{slugify(product['keyword'])}"
    return {
        "id": post_id,
        "date": current_date.isoformat(),
        "scheduled_at": datetime.combine(current_date, time_value).isoformat() + "+03:00",
        "type": "product",
        "platforms": ["facebook", "instagram", "threads", "telegram", "youtube_community"],
        "product": public_product(product),
        "title": product["hook"],
        "cta": f"Напишіть «{product['keyword']}» у Telegram або відкрийте {SITE}",
        "captions": {platform: product_caption(product, platform) for platform in ["facebook", "instagram", "threads", "telegram", "youtube"]},
        "hashtags": hashtags(product),
        "image_prompt": image_prompt(product, "product"),
    }


def build_reel(current_date: date, day_index: int, day_products: list[dict]) -> dict:
    theme = [
        "Як ALT-CAM підбирає рішення безпеки під об’єкт",
        "Товар дня: що дивитися перед покупкою",
        "Камера, домофон, кабель: де найчастіше помиляються",
        "Преміальний монтаж: що має бути в кадрі",
        "Як виглядає система безпеки без хаосу",
        "3 рішення для дому, офісу або складу",
        "Перед покупкою: короткий чек-лист ALT-CAM",
    ][day_index]
    products_text = ", ".join(product["keyword"] for product in day_products)
    post_id = f"altcam-reel-{current_date.isoformat()}-{day_index + 1:02d}"
    scenario = {
        "0-3s": f"Крупний hook на екрані: “{theme}”. Швидкі кадри товарів: {products_text}.",
        "3-10s": "Показати 3 проблеми: не видно обличчя, немає резерву, незручно відкривати двері або хаос у кабелях.",
        "10-20s": "Показати рішення ALT-CAM: товар + монтаж + налаштування + перевірка зі смартфона.",
        "20-30s": "Фінальний кадр: сайт, Telegram-бот, географія Київ / Вишгород / область. Заклик написати ключове слово.",
    }
    caption = (
        f"{theme}\n\n"
        f"Це не просто добірка товарів. Це сценарій: що поставити, де воно має працювати і як не купити зайве.\n\n"
        f"У каруселі: {', '.join(p['product'] for p in day_products)}.\n\n"
        f"Напишіть у Telegram «ПІДБІР» — підкажемо варіант під ваш об’єкт.\n"
        f"🤖 {BOT}\n🌐 {SITE}\n📍 {LOCATION}\n\n"
        f"#AltCam #security #відеоспостереження #домофон #монтаж #Київ #Вишгород"
    )
    return {
        "id": post_id,
        "date": current_date.isoformat(),
        "scheduled_at": datetime.combine(current_date, time(20, 30)).isoformat() + "+03:00",
        "type": "reel_carousel",
        "platforms": ["instagram_reels", "facebook_reels", "tiktok", "youtube_shorts", "telegram"],
        "title": theme,
        "scenario": scenario,
        "carousel_slides": [
            f"Слайд 1: {theme}",
            f"Слайд 2: {day_products[0]['product']} — {day_products[0]['hook']}",
            f"Слайд 3: {day_products[1]['product']} — {day_products[1]['hook']}",
            f"Слайд 4: {day_products[2]['product']} — {day_products[2]['hook']}",
            "Слайд 5: Переваги ALT-CAM — підбір, монтаж, налаштування, підтримка",
            "Слайд 6: CTA — Напишіть «ПІДБІР» у Telegram",
        ],
        "caption": caption,
        "image_prompt": (
            "Create a premium advertising carousel/reels cover for ALT-CAM Security UA: dark anthracite background, "
            "realistic security products, clean yellow CTA, product-card style from user's reference examples, "
            f"theme: {theme}. Include visual places for 3 product tiles and brand resources: website, Telegram, service advantages."
        ),
    }


UPLOADED_MEDIA_POSTS = [
    {
        "filename": "04-ajax.png",
        "category": "Ajax / сигналізація",
        "product": "Ajax для дому та бізнесу",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "квартира / будинок / офіс / магазин",
        "keyword": "AJAX",
        "hook": "Захист, який працює навіть тоді, коли вас немає поруч.",
        "benefits": ["датчики руху й відкриття", "керування зі смартфона", "сирена та push-сповіщення", "підбір сценарію під ваш об’єкт"],
    },
    {
        "filename": "grok-07fd78e8-64bb-4abe-a865-07a943e9a395.jpg",
        "category": "Домофонія",
        "product": "Dahua DHI-VTH2421FW-P 7” PoE",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "квартира / офіс / приватний будинок",
        "keyword": "ДОМОФОН",
        "hook": "Домофон має не просто дзвонити — він має давати контроль входу.",
        "benefits": ["7” сенсорний екран", "PoE-підключення", "робота з відеокамерами", "зручний сценарій для квартири, офісу й будинку"],
    },
    {
        "filename": "grok-4688d7ce-dc63-433c-b569-cf9d7f707359.jpg",
        "category": "PTZ відеоспостереження",
        "product": "Hikvision DS-2DE1C200IW-DE3 mini PTZ",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "двір / вхід / парковка / невеликий бізнес",
        "keyword": "PTZ",
        "hook": "Коли однієї статичної камери мало — потрібен огляд із поворотом.",
        "benefits": ["mini PTZ-формат", "керування напрямком огляду", "IR-підсвітка до 15 м", "зручно для двору, входу або парковки"],
    },
    {
        "filename": "grok-d1dfdfdb-e419-456a-94b6-98158f03a4fe.jpg",
        "category": "PTZ відеоспостереження",
        "product": "Dahua DH-IPC-PTS2249B-E2-S-PV-PRO",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "периметр / склад / паркінг / комерційний об’єкт",
        "keyword": "ПЕРИМЕТР",
        "hook": "Камера, яка не тільки бачить, а й допомагає відлякати порушника.",
        "benefits": ["2+2МП", "WizColor", "активне відлякування до 30 м", "сильне рішення для периметра й бізнесу"],
    },
    {
        "filename": "grok-dbbdd71e-019d-4ef4-b713-2b620597a1fb.jpg",
        "category": "Відеоспостереження",
        "product": "Dahua DH-IPC-HDW2449TM-S-IL",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "магазин / офіс / під’їзд / приватний будинок",
        "keyword": "КАМЕРА",
        "hook": "AI-камера для місць, де важливо бачити деталі, а не просто рух.",
        "benefits": ["4МП", "Smart Dual Light до 30 м", "WizSense AI", "акуратний купольний формат"],
    },
    {
        "filename": "grok-image-0cf4bb1d-db8f-477b-9235-a28aab85ab51.jpg",
        "category": "Wi‑Fi відеоспостереження",
        "product": "Imou Turret SE‑C IPC‑T22EP‑C 1080P",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "квартира / невеликий офіс / кімната / касова зона",
        "keyword": "IMOU",
        "hook": "Коли потрібна проста IP-камера без зайвої складності.",
        "benefits": ["1080P", "кут огляду 92°", "H.265", "детекція руху та ІЧ-підсвітка до 30 м"],
    },
    {
        "filename": "grok-image-148d303a-f438-43ed-89cd-fe5ab84c985e.jpg",
        "category": "Wi‑Fi відеоспостереження",
        "product": "Imou Turret SE‑C IPC‑T22EP‑C 1080P",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "квартира / офіс / невеликий магазин",
        "keyword": "IMOU",
        "hook": "Бюджетна камера може працювати добре — якщо її правильно підібрати й поставити.",
        "benefits": ["2МП Full HD", "детекція руху", "ІЧ-підсвітка", "варіант для базового відеонагляду"],
    },
    {
        "filename": "imagine-381afb84-2c95-46be-8965-b07a4a419850.jpg",
        "category": "Відеоспостереження",
        "product": "Dahua WizMind Triple‑Sight DH-IPC-MFW5241T2-E3-ASE",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "склад / периметр / виробництво / великий двір",
        "keyword": "ТРІПЛ",
        "hook": "Одна точка монтажу — більше контролю по зоні огляду.",
        "benefits": ["Triple‑Sight 3×2МП", "AI-аналітика", "ІЧ до 100 м", "для об’єктів, де сліпі зони коштують дорого"],
    },
    {
        "filename": "imagine-83c076f2-35fb-4852-831c-40d198f3339c.jpg",
        "category": "Домофонія",
        "product": "Dahua DHI-VTH2421FW-P 7” PoE",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "квартира / офіс / ресепшн / приватний будинок",
        "keyword": "ДОМОФОН",
        "hook": "Бачити, хто біля дверей, — це вже не преміум. Це базова безпека.",
        "benefits": ["7” touch-монітор", "PoE", "підключення до 32 камер", "зручний центр керування входом"],
    },
    {
        "filename": "imagine-a8a7fa2a-94a5-4fce-9ca7-169b01ca1d04.jpg",
        "category": "Відеоспостереження",
        "product": "Dahua WizMind Triple‑Sight DH-IPC-MFW5241T2-E3-ASE",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "периметр / склад / логістика / бізнес",
        "keyword": "WIZMIND",
        "hook": "Для серйозного об’єкта потрібна не “просто камера”, а аналітика.",
        "benefits": ["3×2МП", "AI-розпізнавання сценаріїв", "захист IP67", "контроль широкої зони з однієї точки"],
    },
    {
        "filename": "imagine-b5490aab-f026-44b5-8da4-401253e3fb7a.jpg",
        "category": "Відеоспостереження",
        "product": "Hikvision DS-2CD1047G3H-LIUF ColorVu 4МП",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "двір / фасад / вхід / магазин",
        "keyword": "COLORVU",
        "hook": "Нічна картинка має бути кольоровою, якщо вам важливо впізнати деталі.",
        "benefits": ["ColorVu 3.0", "Smart Hybrid Light до 30 м", "4МП", "вдалий варіант для входу, двору й фасаду"],
    },
]


GENERATED_MEDIA_POSTS = [
    {
        "filename": "generated-01-hikvision-colorvu-bullet.jpg",
        "category": "Відеоспостереження",
        "product": "Hikvision DS-2CD1047G3H-LIUF ColorVu 4МП",
        "price": "орієнтир: 7 319 ₴",
        "audience": "двір / фасад / вхід / магазин",
        "keyword": "COLORVU",
        "hook": "Коли вночі потрібно бачити колір, а не сіру пляму.",
        "benefits": ["ColorVu 3.0", "4МП деталізація", "Smart Hybrid Light до 30 м", "мікрофон для контролю ситуації"],
    },
    {
        "filename": "generated-02-indoor-cube-camera.jpg",
        "category": "Відеоспостереження",
        "product": "Hikvision DS-2CD2443G2-I Black 4МП",
        "price": "орієнтир: 5 921 ₴",
        "audience": "квартира / офіс / ресепшн / касова зона",
        "keyword": "ОФІС",
        "hook": "Камера для приміщення, яка не псує інтер’єр і дає нормальну деталізацію.",
        "benefits": ["4МП", "компактний формат", "для офісу або квартири", "зручно контролювати з телефону"],
    },
    {
        "filename": "generated-03-wizmind-nvr.jpg",
        "category": "Відеоспостереження",
        "product": "Dahua DHI-NVR58128H-XI 128-канальний WizMind",
        "price": "орієнтир: 94 520 ₴",
        "audience": "склад / виробництво / великий бізнес / мережа об’єктів",
        "keyword": "NVR",
        "hook": "Коли камер багато, слабкий реєстратор стає вузьким місцем усієї системи.",
        "benefits": ["128 каналів", "8 HDD", "AI-аналітика", "рішення для великих систем відеонагляду"],
    },
    {
        "filename": "generated-04-qr-access-reader.jpg",
        "category": "Контроль доступу",
        "product": "U-PROX SE QR slim",
        "price": "орієнтир: 6 071 ₴",
        "audience": "офіс / бізнес-центр / склад / сервісна зона",
        "keyword": "СКУД",
        "hook": "Доступ без хаосу: QR, картка або брелок — і зрозуміло, хто заходив.",
        "benefits": ["QR-доступ", "RFID-сценарії", "тонкий корпус", "зручно для офісів і комерції"],
    },
    {
        "filename": "generated-05-poe-network-cabinet.jpg",
        "category": "Серверна / монтаж",
        "product": "PoE-комутатор + мережева шафа для IP-камер",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "офіс / магазин / склад / приватний будинок",
        "keyword": "PoE",
        "hook": "Акуратна мережа — це коли камери працюють стабільно, а не “як пощастить”.",
        "benefits": ["живлення камер по кабелю", "порядок у шафі", "зручне обслуговування", "менше випадкових відключень"],
    },
    {
        "filename": "generated-06-ups-backup-power.jpg",
        "category": "Резервне живлення",
        "product": "UPS / резервне живлення для камер, роутера та NVR",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "будинок / офіс / магазин / склад",
        "keyword": "РЕЗЕРВ",
        "hook": "Світло зникло — а відеонагляд і інтернет мають працювати далі.",
        "benefits": ["резерв для камер", "живлення роутера/NVR", "менше простоїв", "підбір під час автономної роботи"],
    },
    {
        "filename": "generated-07-ip-call-panel.jpg",
        "category": "Домофонія",
        "product": "IP виклична панель для хвіртки або входу",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "приватний будинок / офіс / ЖК / ворота",
        "keyword": "ПАНЕЛЬ",
        "hook": "Відкривати двері потрібно тільки тому, кого ви бачите.",
        "benefits": ["відеовиклик", "зв’язок зі смартфоном", "сценарій для хвіртки або входу", "можна інтегрувати з електрозамком"],
    },
    {
        "filename": "generated-08-thermal-perimeter-camera.jpg",
        "category": "Тепловізійне відеоспостереження",
        "product": "Тепловізійна камера для периметра",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "склад / промисловий об’єкт / периметр / поле огляду без світла",
        "keyword": "ПЕРИМЕТР",
        "hook": "Якщо об’єкт великий, периметр треба бачити навіть у темряві й тумані.",
        "benefits": ["контроль периметра", "робота в складному освітленні", "менше сліпих зон", "підбір під реальну відстань"],
    },
    {
        "filename": "generated-09-ajax-security-kit.jpg",
        "category": "Ajax / сигналізація",
        "product": "Ajax комплект для дому або бізнесу",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "квартира / будинок / офіс / магазин",
        "keyword": "AJAX",
        "hook": "Сигналізація має попереджати раніше, ніж проблема стане збитками.",
        "benefits": ["датчики руху", "датчики відкриття", "сирена", "керування через застосунок"],
    },
    {
        "filename": "generated-10-installer-service.jpg",
        "category": "Монтаж / сервіс",
        "product": "Підбір, монтаж і налаштування систем безпеки ALT-CAM",
        "price": "ціну уточнюємо перед публікацією",
        "audience": "дім / офіс / склад / магазин / ЖК",
        "keyword": "ПІДБІР",
        "hook": "Обладнання важливе. Але правильний монтаж вирішує, чи буде система працювати.",
        "benefits": ["виїзд і оцінка задачі", "підбір обладнання", "акуратний монтаж", "налаштування доступу зі смартфона"],
    },
]


REEL_MEDIA = [
    "altcam-reel-2026-08-10-01.jpg",
    "altcam-reel-2026-08-11-02.jpg",
    "altcam-reel-2026-08-12-03.jpg",
    "altcam-reel-2026-08-13-04.jpg",
    "altcam-reel-2026-08-14-05.jpg",
    "altcam-reel-2026-08-15-06.jpg",
    "altcam-reel-2026-08-16-07.jpg",
]


def apply_uploaded_media_content(plan: dict) -> None:
    product_posts = [post for post in plan["posts"] if post["type"] == "product"]
    for post, product in zip(product_posts, [*UPLOADED_MEDIA_POSTS, *GENERATED_MEDIA_POSTS]):
        post["product"] = public_product(product)
        post["title"] = product["hook"]
        post["cta"] = f"Напишіть «{product['keyword']}» у Telegram або відкрийте {SITE}"
        post["captions"] = {platform: product_caption(product, platform) for platform in ["facebook", "instagram", "threads", "telegram", "youtube"]}
        post["hashtags"] = hashtags(product)
        post["image_prompt"] = image_prompt(product, "product")
        post["media_type"] = "image"
        post["media_path"] = f"media/square/{product['filename']}"
        post["media_status"] = "ready"
        post["media_note"] = "медіа завантажено користувачем і текст адаптовано під цю картинку"
        post["media_requirements"] = "готова квадратна картинка для Facebook / Instagram / Telegram / Threads / YouTube Community"
        post["uploaded_media_filename"] = product["filename"]
    for post, filename in zip([post for post in plan["posts"] if post["type"] == "reel_carousel"], REEL_MEDIA):
        post["media_type"] = "image"
        post["media_path"] = f"media/vertical/{filename}"
        post["media_status"] = "ready"
        post["media_note"] = "готова вертикальна обкладинка; відео/карусель монтуємо за сценарієм"
        post["media_requirements"] = "готова обкладинка 9:16 для Reels / TikTok / Shorts"


def build_plan() -> dict:
    start = date(2026, 8, 10)
    times = [time(10, 0), time(14, 0), time(18, 0)]
    posts = []
    product_index = 0
    for day_index in range(7):
        current = start + timedelta(days=day_index)
        day_products = PRODUCTS[product_index : product_index + 3]
        for slot, product in enumerate(day_products):
            posts.append(build_post(product, current, times[slot], slot + 1))
        posts.append(build_reel(current, day_index, day_products))
        product_index += 3
    return {
        "brand": "ALT-CAM Security UA",
        "period": "2026-08-10 — 2026-08-16",
        "timezone": "Europe/Kyiv",
        "posting_rule": "3 товарні пости щодня + 1 Reels/карусель щодня",
        "posts": posts,
    }


def prepare_manual_media_slots(plan: dict) -> None:
    square_dir = MEDIA_DIR / "square"
    vertical_dir = MEDIA_DIR / "vertical"
    square_dir.mkdir(parents=True, exist_ok=True)
    vertical_dir.mkdir(parents=True, exist_ok=True)
    for post in plan["posts"]:
        if post["type"] == "product":
            path = square_dir / f"{post['id']}.jpg"
            post["media_type"] = "image"
            post["media_path"] = str(path.relative_to(OUT_DIR).as_posix())
            post["media_status"] = "awaiting_upload"
            post["media_note"] = "завантажте власне квадратне медіа 1:1 з таким іменем файлу"
            post["media_requirements"] = "JPG/PNG, 1080×1080, без згадки постачальників"
        else:
            path = vertical_dir / f"{post['id']}.mp4"
            post["media_type"] = "video"
            post["media_path"] = str(path.relative_to(OUT_DIR).as_posix())
            post["media_status"] = "awaiting_upload"
            post["media_note"] = "завантажте власне вертикальне відео 9:16 з таким іменем файлу"
            post["media_requirements"] = "MP4, 1080×1920, 10–30 секунд, перші 3 секунди з сильним гачком"


def write_prompts(plan: dict) -> None:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    for post in plan["posts"]:
        path = PROMPTS_DIR / f"{post['id']}.md"
        if post["type"] == "product":
            body = f"# {post['title']}\n\n{post['image_prompt']}\n\n## Текстові зони\n\nCTA: {post['cta']}\n\n## Caption Instagram\n\n{post['captions']['instagram']}\n"
        else:
            body = f"# {post['title']}\n\n{post['image_prompt']}\n\n## Сценарій\n\n" + "\n".join(f"- {k}: {v}" for k, v in post["scenario"].items()) + "\n\n## Caption\n\n" + post["caption"] + "\n"
        path.write_text(body, encoding="utf-8")
        post["prompt_path"] = str(path.relative_to(OUT_DIR).as_posix())


def write_publishing_posts(plan: dict) -> None:
    ready_posts = []
    for post in plan["posts"]:
        item = {
            "id": post["id"],
            "scheduled_at": post["scheduled_at"],
            "platforms": post["platforms"],
            "status": "ready",
            "approval_required": True,
            "media_type": post["media_type"],
            "media_path": post["media_path"],
            "media_status": post["media_status"],
            "media_note": post["media_note"],
            "media_requirements": post["media_requirements"],
        }
        if post["type"] == "product":
            item["captions"] = post["captions"]
            item["caption"] = post["captions"]["instagram"]
        else:
            item["caption"] = post["caption"]
            item["scenario"] = post["scenario"]
            item["carousel_slides"] = post["carousel_slides"]
        ready_posts.append(item)
    PUBLISHING_PATH.write_text(json.dumps({"posts": ready_posts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_md(plan: dict) -> str:
    lines = [
        "# ALT-CAM — тижневий товарний контент-план",
        "",
        f"Період: **{plan['period']}**",
        "",
        "Правило: **3 товарні пости щодня + 1 Reels/карусель щодня**.",
        "",
        "CTA: сайт `https://alt-cam.net.ua` або Telegram-бот `https://t.me/alt_cam_bot`.",
        "",
    ]
    for post in plan["posts"]:
        lines.extend([
            f"## {post['scheduled_at']} — {post['title']}",
            "",
            f"- Тип: {post['type']}",
            f"- Платформи: {', '.join(post['platforms'])}",
        ])
        if post["type"] == "product":
            product = post["product"]
            lines.extend([
                f"- Товар: {product['product']}",
                f"- Категорія: {product['category']}",
                f"- Ціна: {product['price']}",
                f"- Медіа: `{post['media_path']}`",
                f"- Статус медіа: {post['media_note']}",
                f"- Prompt: [{post['prompt_path']}]({post['prompt_path']})",
                "",
                "### Facebook",
                "",
                post["captions"]["facebook"],
                "",
                "### Instagram",
                "",
                post["captions"]["instagram"],
                "",
                "### Threads",
                "",
                post["captions"]["threads"],
                "",
                "### Telegram",
                "",
                post["captions"]["telegram"],
                "",
            ])
        else:
            lines.extend([
                f"- Медіа: `{post['media_path']}`",
                f"- Статус медіа: {post['media_note']}",
                f"- Prompt: [{post['prompt_path']}]({post['prompt_path']})",
                "",
                "### Сценарій",
                "",
            ])
            for key, value in post["scenario"].items():
                lines.append(f"- **{key}:** {value}")
            lines.extend([
                "",
                "### Карусель",
                "",
                *[f"- {slide}" for slide in post["carousel_slides"]],
                "",
                "### Caption",
                "",
                post["caption"],
                "",
            ])
    return "\n".join(lines) + "\n"


def render_calendar_html() -> str:
    return """<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ALT-CAM товарний тиждень</title>
  <style>
    :root { color-scheme: dark; --bg:#121212; --panel:rgba(255,255,255,.045); --line:rgba(255,255,255,.12); --text:#F5F5F7; --muted:#96969B; --gold:#FFCC00; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, system-ui, Segoe UI, sans-serif; background: radial-gradient(circle at top left, rgba(255,204,0,.13), transparent 36rem), var(--bg); color:var(--text); }
    main { width:min(1180px, calc(100% - 32px)); margin:0 auto; padding:42px 0 64px; }
    header { display:flex; justify-content:space-between; gap:20px; align-items:flex-end; margin-bottom:24px; }
    h1 { font-size:clamp(30px,5vw,54px); margin:0 0 8px; letter-spacing:-.04em; }
    p { color:var(--muted); line-height:1.55; margin:0; }
    .badge, .chip, a.chip { border:1px solid var(--line); background:var(--panel); border-radius:999px; padding:8px 11px; color:var(--text); text-decoration:none; display:inline-flex; gap:6px; align-items:center; }
    .toolbar { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }
    .grid { display:grid; gap:16px; }
    .day { border:1px solid var(--line); border-radius:22px; overflow:hidden; background:var(--panel); }
    .day-head { padding:18px 20px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:12px; background:rgba(255,255,255,.035); }
    h2 { font-size:19px; margin:0; }
    .post { display:grid; grid-template-columns:92px 190px 1fr; gap:16px; padding:18px 20px; border-bottom:1px solid var(--line); }
    .post:last-child { border-bottom:0; }
    .time { color:var(--gold); font-weight:900; font-size:18px; }
    img.media { width:190px; aspect-ratio:1/1; object-fit:cover; border-radius:18px; border:1px solid var(--line); background:#222; }
    img.media.vertical, video.media.vertical { aspect-ratio:9/16; }
    video.media { width:190px; aspect-ratio:1/1; object-fit:cover; border-radius:18px; border:1px solid var(--line); background:#222; }
    .media-wrap { width:190px; }
    .media-slot { width:190px; min-height:190px; border:1px dashed rgba(255,204,0,.55); border-radius:18px; background:rgba(255,204,0,.07); padding:14px; display:none; flex-direction:column; justify-content:center; gap:8px; color:var(--text); }
    .media-slot.vertical { min-height:338px; }
    .media-slot b { color:var(--gold); font-size:13px; text-transform:uppercase; letter-spacing:.08em; }
    .media-slot code { color:var(--text); word-break:break-word; font-size:12px; }
    .media-slot small { color:var(--muted); line-height:1.35; }
    h3 { margin:0 0 8px; font-size:21px; }
    .meta { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0; }
    details { margin-top:10px; border:1px solid var(--line); border-radius:14px; overflow:hidden; background:rgba(0,0,0,.18); }
    summary { cursor:pointer; padding:12px 14px; color:var(--gold); font-weight:800; }
    pre { white-space:pre-wrap; margin:0; padding:0 14px 14px; font-family:inherit; line-height:1.5; }
    @media (max-width:720px){ header{display:block}.badge{margin-top:16px}.post{grid-template-columns:1fr}.media-wrap,img.media,video.media,.media-slot{width:100%;max-height:420px;} }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>ALT-CAM товарний тиждень</h1>
      <p>3 товарні пости щодня + 1 Reels/карусель. Тексти готові, медіа додаються вручну у папку за вказаними іменами файлів.</p>
    </div>
    <div class="badge">10–16 серпня 2026</div>
  </header>
  <nav class="toolbar">
    <a class="chip" href="./index.html">60-денний календар</a>
    <a class="chip" href="../content-plans/2026-08-10-product-week/PLAN.md">PLAN.md</a>
    <a class="chip" href="../content-plans/2026-08-10-product-week/publishing-posts.json">publishing-posts.json</a>
  </nav>
  <section id="calendar" class="grid"></section>
</main>
<script src="./product-week-data.js"></script>
<script>
const calendar = document.getElementById('calendar');
const fmtDate = new Intl.DateTimeFormat('uk-UA', {weekday:'long', day:'numeric', month:'long', timeZone:'Europe/Kyiv'});
const fmtTime = new Intl.DateTimeFormat('uk-UA', {hour:'2-digit', minute:'2-digit', timeZone:'Europe/Kyiv'});
function esc(v){ return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
function block(label, text){ return `<details><summary>${label}</summary><pre>${esc(text)}</pre></details>`; }
function mediaBlock(post){
  const src = `../content-plans/2026-08-10-product-week/${post.media_path}`;
  const vertical = post.type === 'reel_carousel';
  const slot = `<div class="media-slot ${vertical ? 'vertical' : ''}"><b>очікує ваше медіа</b><code>${esc(post.media_path)}</code><small>${esc(post.media_requirements || post.media_note)}</small></div>`;
  if (post.media_type === 'video') {
    return `<div class="media-wrap"><video class="media ${vertical ? 'vertical' : ''}" src="${src}" controls onerror="this.nextElementSibling.style.display='flex';this.remove()"></video>${slot}</div>`;
  }
  return `<div class="media-wrap"><img class="media" src="${src}" alt="" onerror="this.nextElementSibling.style.display='flex';this.remove()">${slot}</div>`;
}
const days = new Map();
for (const post of window.ALT_CAM_PRODUCT_WEEK.posts) {
  const key = post.scheduled_at.slice(0,10);
  if (!days.has(key)) days.set(key, []);
  days.get(key).push(post);
}
calendar.innerHTML = [...days.entries()].map(([key, posts]) => `
  <article class="day">
    <div class="day-head"><h2>${fmtDate.format(new Date(posts[0].scheduled_at))}</h2><div class="badge">${posts.length} публікації</div></div>
    ${posts.map(post => `
      <div class="post">
        <div class="time">${fmtTime.format(new Date(post.scheduled_at))}</div>
        ${mediaBlock(post)}
        <div>
          <h3>${esc(post.title)}</h3>
          <p>${esc(post.type === 'product' ? post.product.product : post.carousel_slides[0])}</p>
          <div class="meta">
            <span class="chip">${post.type}</span>
            ${post.platforms.map(p => `<span class="chip">${p}</span>`).join('')}
            <span class="chip">${post.media_status === 'awaiting_upload' ? 'медіа: додати вручну' : 'медіа готове'}</span>
            <a class="chip" href="../content-plans/2026-08-10-product-week/media/">папка media</a>
          </div>
          ${post.type === 'product' ? block('Facebook', post.captions.facebook) + block('Instagram', post.captions.instagram) + block('Threads', post.captions.threads) + block('Telegram', post.captions.telegram) + block('YouTube Community', post.captions.youtube) : block('Reels / TikTok / Shorts сценарій', Object.entries(post.scenario).map(([k,v]) => `${k}: ${v}`).join('\\n')) + block('Карусель', post.carousel_slides.join('\\n')) + block('Caption', post.caption)}
        </div>
      </div>
    `).join('')}
  </article>
`).join('');
</script>
</body>
</html>
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    plan = build_plan()
    prepare_manual_media_slots(plan)
    apply_uploaded_media_content(plan)
    write_prompts(plan)
    write_publishing_posts(plan)
    (OUT_DIR / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "PLAN.md").write_text(render_md(plan), encoding="utf-8")
    DATA_PATH.write_text("window.ALT_CAM_PRODUCT_WEEK = " + json.dumps(plan, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    HTML_PATH.write_text(render_calendar_html(), encoding="utf-8")
    print(OUT_DIR)
    print(HTML_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
