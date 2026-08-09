from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week"
PROMPTS_DIR = OUT_DIR / "image-prompts"
CALENDAR_DIR = ROOT / "social-posts" / "calendar"
DATA_PATH = CALENDAR_DIR / "product-week-data.js"
HTML_PATH = CALENDAR_DIR / "product-week.html"

SITE = "https://alt-cam.net.ua"
BOT = "https://t.me/alt_cam_bot"
LOCATION = "Київ • Вишгород • Київська область"
HASHTAGS_BASE = "#AltCam #відеоспостереження #системибезпеки #монтажкамер #домофон #Ajax #Київ #Вишгород"


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
        "benefits": ["4МП деталізація", "компактний корпус", "підходить для офісу й квартири", "зручно показати в premium product-card"],
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


def price_line(product: dict) -> str:
    return f"Ціна: {product['price']}. Перед публікацією фінальну ціну підтверджуємо по наявності та комплектації."


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


def build_post(product: dict, current_date: date, time_value: time, index: int) -> dict:
    post_id = f"altcam-product-{current_date.isoformat()}-{index:02d}-{slugify(product['keyword'])}"
    return {
        "id": post_id,
        "date": current_date.isoformat(),
        "scheduled_at": datetime.combine(current_date, time_value).isoformat() + "+03:00",
        "type": "product",
        "platforms": ["facebook", "instagram", "threads", "telegram", "youtube_community"],
        "product": product,
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
        "sources": [
            "https://viatec.ua/ru",
            "https://neolight.in.ua/uk",
            "https://yugtorg.bigopt.com/",
        ],
        "posts": posts,
    }


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
                f"- Джерело: [{product['source']}]({product['source_url']})",
                f"- Ціна: {product['price']}",
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
    .post { display:grid; grid-template-columns:92px 1fr; gap:16px; padding:18px 20px; border-bottom:1px solid var(--line); }
    .post:last-child { border-bottom:0; }
    .time { color:var(--gold); font-weight:900; font-size:18px; }
    h3 { margin:0 0 8px; font-size:21px; }
    .meta { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0; }
    details { margin-top:10px; border:1px solid var(--line); border-radius:14px; overflow:hidden; background:rgba(0,0,0,.18); }
    summary { cursor:pointer; padding:12px 14px; color:var(--gold); font-weight:800; }
    pre { white-space:pre-wrap; margin:0; padding:0 14px 14px; font-family:inherit; line-height:1.5; }
    @media (max-width:720px){ header{display:block}.badge{margin-top:16px}.post{grid-template-columns:1fr} }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>ALT-CAM товарний тиждень</h1>
      <p>3 товарні пости щодня + 1 Reels/карусель. Стиль: premium product-card, як у прикладах.</p>
    </div>
    <div class="badge">10–16 серпня 2026</div>
  </header>
  <nav class="toolbar">
    <a class="chip" href="./index.html">60-денний календар</a>
    <a class="chip" href="../content-plans/2026-08-10-product-week/PLAN.md">PLAN.md</a>
    <a class="chip" href="../content-plans/2026-08-10-product-week/image-prompts/">Image prompts</a>
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
        <div>
          <h3>${esc(post.title)}</h3>
          <p>${esc(post.type === 'product' ? post.product.product : post.carousel_slides[0])}</p>
          <div class="meta">
            <span class="chip">${post.type}</span>
            ${post.platforms.map(p => `<span class="chip">${p}</span>`).join('')}
            <a class="chip" href="../content-plans/2026-08-10-product-week/${post.prompt_path}">prompt</a>
            ${post.type === 'product' ? `<a class="chip" href="${post.product.source_url}">${post.product.source}</a>` : ''}
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
    write_prompts(plan)
    (OUT_DIR / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "PLAN.md").write_text(render_md(plan), encoding="utf-8")
    DATA_PATH.write_text("window.ALT_CAM_PRODUCT_WEEK = " + json.dumps(plan, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    HTML_PATH.write_text(render_calendar_html(), encoding="utf-8")
    print(OUT_DIR)
    print(HTML_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
