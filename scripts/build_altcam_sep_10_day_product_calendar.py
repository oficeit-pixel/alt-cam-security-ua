from __future__ import annotations

import json
import shutil
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from textwrap import dedent

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - fallback is handled at runtime
    Image = None
    ImageDraw = None
    ImageFont = None


ROOT = Path(__file__).resolve().parents[1]
LOCAL_ASSET_ROOT = Path(r"C:\Users\Net_w\Documents\New project")
PLAN_ID = "2026-09-10-10-day-product-presentation"
OUT = ROOT / "social-posts" / "content-plans" / PLAN_ID
CALENDAR_HTML = ROOT / "social-posts" / "calendar" / "sep-10-day-product-posts.html"
CALENDAR_DATA = ROOT / "social-posts" / "calendar" / "sep-10-day-product-posts-data.js"
BOT_URL = "https://t.me/alt_cam_bot"
SITE_URL = "https://alt-cam.net.ua"
TZ = timezone(timedelta(hours=3), name="Europe/Kyiv")


REFERENCE_IMAGES = [
    Path(r"C:\Users\Net_w\Downloads\ChatGPT Image 4 сент. 2026 г., 09_51_54.png"),
    Path(r"C:\Users\Net_w\Downloads\ChatGPT Image 4 сент. 2026 г., 01_14_44.png"),
    Path(r"C:\Users\Net_w\Downloads\Сгенерированное изображение 1 (1).png"),
    Path(r"C:\Users\Net_w\Downloads\Сгенерированное изображение 4.png"),
    Path(r"C:\Users\Net_w\Downloads\Сгенерированное изображение 2 (3).png"),
    Path(r"D:\Тут та зараз\ChatGPT Image 4 июл. 2026 г., 08_53_36.png"),
]

PERSON_IMAGES = [
    Path(r"C:\Users\Net_w\Downloads\Сгенерированное изображение 4.png"),
    Path(r"C:\Users\Net_w\Downloads\Сгенерированное изображение 2 (3).png"),
    Path(r"C:\Users\Net_w\Downloads\Сгенерированное изображение 1 (1).png"),
    Path(r"C:\Users\Net_w\Documents\New project\social-posts\brand-assets\grok-video-source\11-installer-uniform-reference.png"),
    Path(r"C:\Users\Net_w\Documents\New project\social-posts\brand-assets\grok-video-source\12-installer-installation-scene-reference.png"),
]


HASHTAGS_BASE = [
    "#altcam",
    "#altcamsecurityua",
    "#відеоспостереженнякиїв",
    "#монтажкамер",
    "#безпекабудинку",
    "#київ",
    "#вишгород",
    "#київськаобласть",
]

ASSET_POOLS = {
    "Резервне живлення": [
        "social-posts/instagram-catalog/product-photos/backup/01.webp",
        "social-posts/instagram-catalog/product-photos/backup/04.jpg",
        "social-posts/brand-assets/marketing-scenes/backup-bright.png",
    ],
    "Стабілізація напруги": [
        "social-posts/instagram-catalog/product-photos/backup/02.webp",
        "social-posts/instagram-catalog/product-photos/backup/03.webp",
        "social-posts/brand-assets/marketing-scenes/backup-bright.png",
    ],
    "LiFePO4 акумулятори": [
        "social-posts/instagram-catalog/product-photos/backup/05.jpg",
        "social-posts/instagram-catalog/product-photos/backup/06.webp",
        "social-posts/brand-assets/marketing-scenes/backup-bright.png",
    ],
    "Відеоспостереження": [
        "social-posts/instagram-catalog/product-photos/cameras/01.webp",
        "social-posts/instagram-catalog/product-photos/cameras/02.webp",
        "social-posts/instagram-catalog/product-photos/cameras/04.webp",
        "social-posts/brand-assets/marketing-scenes/cameras-exterior-bright.png",
    ],
    "Міні PTZ": [
        "social-posts/instagram-catalog/product-photos/cameras/02.webp",
        "social-posts/instagram-catalog/product-photos/cameras/09.webp",
        "social-posts/brand-assets/marketing-scenes/cameras-bright.png",
    ],
    "Домофонія": [
        "social-posts/instagram-catalog/product-photos/intercoms/01.webp",
        "social-posts/instagram-catalog/product-photos/intercoms/02.webp",
        "social-posts/instagram-catalog/product-photos/intercoms/08.jpg",
        "social-posts/brand-assets/marketing-scenes/access-exterior-reader-bright.png",
    ],
    "СКУД": [
        "social-posts/brand-assets/marketing-scenes/access-bright.png",
        "social-posts/brand-assets/marketing-scenes/access-exterior-reader-bright.png",
        "social-posts/brand-assets/marketing-scenes/access-interior-exit-bright.png",
    ],
    "Ajax": [
        "social-posts/instagram-catalog/product-photos/ajax/01.jpg",
        "social-posts/instagram-catalog/product-photos/ajax/06.webp",
        "social-posts/brand-assets/marketing-scenes/ajax-hub-bright.png",
    ],
    "NVR": [
        "social-posts/instagram-catalog/product-photos/recorders/01.webp",
        "social-posts/instagram-catalog/product-photos/recorders/02.webp",
        "social-posts/brand-assets/marketing-scenes/cameras-interior-bright.png",
    ],
    "PoE мережа": [
        "social-posts/instagram-catalog/product-photos/recorders/04.jpg",
        "social-posts/instagram-catalog/product-photos/recorders/06.webp",
        "social-posts/brand-assets/marketing-scenes/cameras-interior-bright.png",
    ],
    "Кабель": [
        "social-posts/brand-assets/grok-video-source/12-installer-installation-scene-reference.png",
        "social-posts/brand-assets/marketing-scenes/cameras-interior-bright.png",
    ],
    "Монтажні аксесуари": [
        "social-posts/brand-assets/grok-video-source/12-installer-installation-scene-reference.png",
        "social-posts/brand-assets/marketing-scenes/cameras-exterior-bright.png",
    ],
    "Інструмент": [
        "social-posts/brand-assets/grok-video-source/12-installer-installation-scene-reference.png",
        "social-posts/brand-assets/grok-video-source/11-installer-uniform-reference.png",
    ],
    "Аудит системи": [
        "social-posts/brand-assets/grok-video-source/11-installer-uniform-reference.png",
        "social-posts/brand-assets/marketing-scenes/cameras-bright.png",
    ],
    "Комплект під ключ": [
        "social-posts/brand-assets/grok-video-source/11-installer-uniform-reference.png",
        "social-posts/brand-assets/marketing-scenes/ajax-bright.png",
    ],
    "Сервіс": [
        "social-posts/brand-assets/grok-video-source/12-installer-installation-scene-reference.png",
        "social-posts/brand-assets/marketing-scenes/cameras-interior-bright.png",
    ],
}


PRODUCTS = [
    {
        "topic": "Резервне живлення",
        "brand": "Victron Energy",
        "product": "MultiPlus-II 48/5000/70-50",
        "hook": "Коли світло зникає — система безпеки має працювати далі.",
        "pain": "Камери, домофон і роутер часто вимикаються саме тоді, коли потрібен запис.",
        "solution": "Інвертор із чистою синусоїдою тримає критичне обладнання без ризику для електроніки.",
        "specs": ["48 В", "до 4000 Вт при 25°C", "зарядний пристрій 70 А", "чиста синусоїда 230 В"],
        "audience": "котедж / офіс / серверна / охоронна система",
        "keyword": "РЕЗЕРВ",
        "visual": "Сергій у шоурумі поруч із синім інвертором, великий герой-продукт на передньому плані",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Стабілізація напруги",
        "brand": "KEBO",
        "product": "IVR-550VA 2xShuko",
        "hook": "Стрибки напруги тихо вбивають техніку — поки не стає пізно.",
        "pain": "Реєстратор, роутер або блок живлення можуть перезавантажуватись без видимої причини.",
        "solution": "Стабілізатор вирівнює напругу і дає обладнанню працювати стабільно.",
        "specs": ["550 Вт", "вхід 90–310 В AC", "вихід 220/230 В ±2%", "2 розетки Shuko"],
        "audience": "квартира / невеликий офіс / роутер / відеореєстратор",
        "keyword": "НАПРУГА",
        "visual": "Аліса показує стабілізатор на столі, фон — преміальний шоурум ALT-CAM",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "LiFePO4 акумулятори",
        "brand": "Deye",
        "product": "RW-M6.1 LiFePO4",
        "hook": "UPS на 20 хвилин — це не резерв. Це пауза перед проблемою.",
        "pain": "Для камер, Ajax, Wi‑Fi і домофонії потрібні години автономії, а не кілька хвилин.",
        "solution": "LiFePO4 батарея дає довгий ресурс, стабільну ємність і безпечну роботу.",
        "specs": ["6,14 кВт·год", "51,2 В", "LiFePO4", "настінний або підлоговий монтаж"],
        "audience": "будинок / бізнес / склад / система безпеки",
        "keyword": "АВТОНОМІЯ",
        "visual": "товарна презентація батареї біля стіни, Сергій пояснює схему підключення",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Відеоспостереження",
        "brand": "Hikvision",
        "product": "DS-2CD1047G3H-LIUF ColorVu",
        "hook": "Чорно-біла нічна картинка — не доказ, якщо деталей не видно.",
        "pain": "У темряві важливо бачити колір авто, одяг і напрямок руху.",
        "solution": "ColorVu дає кольорове зображення вночі та допомагає швидше розпізнати подію.",
        "specs": ["4 МП", "ColorVu", "вбудований мікрофон", "Smart Hybrid Light"],
        "audience": "двір / вхід / фасад / приватний будинок",
        "keyword": "КОЛІР ВНОЧІ",
        "visual": "нічний двір, камера на фасаді, порівняння звичайної та кольорової картинки",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Відеоспостереження",
        "brand": "Dahua",
        "product": "DH-IPC-PTS2249B-E2-S-PV-PRO",
        "hook": "Камера може не тільки бачити, а й відлякувати.",
        "pain": "На складах і парковках реакція після події часто запізнюється.",
        "solution": "Активне відлякування, WizColor і керування оглядом допомагають зупинити порушника раніше.",
        "specs": ["2+2 МП", "WizColor", "активне відлякування до 30 м", "PTZ-огляд"],
        "audience": "периметр / склад / паркінг / комерційний об’єкт",
        "keyword": "ПЕРИМЕТР",
        "visual": "камера на темному периметрі складу, червоно-синя підсвітка, динамічна сцена",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Міні PTZ",
        "brand": "Hikvision",
        "product": "DS-2DE1C200IW-DE3 mini PTZ",
        "hook": "Однієї статичної камери мало, коли треба бачити більше кута.",
        "pain": "Вхід, хвіртка і парковка часто випадають із одного кадру.",
        "solution": "Міні PTZ дозволяє змінювати напрямок огляду й контролювати ключові зони.",
        "specs": ["mini PTZ", "IR до 15 м", "керування напрямком", "компактний корпус"],
        "audience": "двір / вхід / невеликий бізнес / паркування",
        "keyword": "PTZ",
        "visual": "камера на фасаді приватного будинку, стрілки огляду, смартфон із керуванням",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Домофонія",
        "brand": "Dahua",
        "product": "DHI-VTH2421FW-P",
        "hook": "Двері потрібно відкривати тільки тому, кого ви бачите.",
        "pain": "Звичайний дзвінок не дає контролю й запису події.",
        "solution": "IP-монітор показує виклик, дає двосторонній зв’язок і інтегрується зі смартфоном.",
        "specs": ["7″ IPS", "PoE", "двосторонній зв’язок", "відкриття замка"],
        "audience": "квартира / офіс / приватний будинок / під’їзд",
        "keyword": "ДОМОФОН",
        "visual": "відеодомофон у сучасному холі, відвідувач на екрані, рука зі смартфоном",
        "source_url": "https://viatec.ua/ru/product/DHI-VTH2421FW-P",
    },
    {
        "topic": "Домофонія",
        "brand": "Hikvision",
        "product": "DS-KH6110-WE1",
        "hook": "Контроль входу має бути в телефоні, а не тільки на стіні.",
        "pain": "Коли вас немає вдома, виклик біля дверей може залишитись без відповіді.",
        "solution": "Wi‑Fi домофон дозволяє приймати виклики та відкривати двері зі смартфона.",
        "specs": ["4,3″ екран", "Wi‑Fi", "Hik-Connect", "керування замком"],
        "audience": "квартира / невеликий офіс / орендний об’єкт",
        "keyword": "ВХІД",
        "visual": "Аліса біля внутрішнього монітора, на телефоні — виклик із дверей",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "СКУД",
        "brand": "U-Prox",
        "product": "SE QR Slim",
        "hook": "Ключі губляться. QR-доступ — керований і тимчасовий.",
        "pain": "Для офісу або ЖК складно контролювати, хто і коли має доступ.",
        "solution": "Зчитувач QR/BLE/NFC допомагає видавати доступ без хаосу з ключами.",
        "specs": ["QR", "BLE", "NFC", "тонкий корпус"],
        "audience": "офіс / ЖК / склад / орендний бізнес",
        "keyword": "ДОСТУП",
        "visual": "турнікет або двері офісу, смартфон із QR, жовті акценти доступу",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Ajax",
        "brand": "Ajax",
        "product": "Hub + MotionProtect + DoorProtect",
        "hook": "Квартира під захистом навіть тоді, коли нікого немає вдома.",
        "pain": "Небезпечний не сам факт злому, а те, що ви дізнаєтесь про нього запізно.",
        "solution": "Ajax миттєво повідомляє про рух, відкриття дверей/вікон і тривогу.",
        "specs": ["Hub", "датчики руху", "датчики відкриття", "сирена / брелок / застосунок"],
        "audience": "квартира / будинок / офіс / магазин",
        "keyword": "AJAX",
        "visual": "преміальна квартира, Ajax Hub і датчики біля дверей, смартфон із застосунком",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "NVR",
        "brand": "Dahua",
        "product": "NVR AI-серії для бізнесу",
        "hook": "Камери без нормального реєстратора — це просто картинки.",
        "pain": "Без архіву, пошуку подій і стабільного запису важко знайти потрібний момент.",
        "solution": "NVR із AI-функціями допомагає зберігати архів і швидше знаходити події.",
        "specs": ["IP-канали", "AI-пошук", "H.265+", "місце під HDD"],
        "audience": "магазин / склад / СТО / офіс",
        "keyword": "АРХІВ",
        "visual": "серверна шафа, NVR на полиці, монітор із камерами та таймлайном подій",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "PoE мережа",
        "brand": "Ewind",
        "product": "PoE-комутатор 8 портів",
        "hook": "Один кабель — і живлення, і відео для камери.",
        "pain": "Окремі блоки живлення біля кожної камери створюють хаос і слабкі місця.",
        "solution": "PoE-комутатор живить камери централізовано та спрощує монтаж.",
        "specs": ["8 PoE-портів", "uplink", "живлення камер", "акуратна серверна"],
        "audience": "будинок / офіс / магазин / невеликий склад",
        "keyword": "PoE",
        "visual": "акуратний щит зі свічем, жовті патчкорди, монтажник підписує кабелі",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Кабель",
        "brand": "Cat.6",
        "product": "UTP/FTP кабель для відеонагляду",
        "hook": "Поганий кабель може зіпсувати навіть дорогу камеру.",
        "pain": "Зависання, втрати відео і перезавантаження часто починаються не з камери, а з лінії.",
        "solution": "Підбираємо кабель під довжину, PoE-навантаження, вулицю або приміщення.",
        "specs": ["Cat.5e/Cat.6", "мідь або CCA", "зовнішня оболонка", "PoE-сумісність"],
        "audience": "будь-яка система відеоспостереження",
        "keyword": "КАБЕЛЬ",
        "visual": "рулони кабелю, патчкорди, маркування ліній, рука монтажника з тестером",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Монтажні аксесуари",
        "brand": "Універсальні кронштейни",
        "product": "Кронштейни та монтажні коробки для камер",
        "hook": "Камера має виглядати як частина об’єкта, а не як тимчасове рішення.",
        "pain": "Відкриті дроти, неправильний кут і слабке кріплення псують і вигляд, і безпеку.",
        "solution": "Підбираємо коробки, кронштейни, гермовводи й кріплення під конкретну поверхню.",
        "specs": ["настінні кронштейни", "монтажні коробки", "герметизація", "антивандальний монтаж"],
        "audience": "фасад / паркан / під’їзд / офіс",
        "keyword": "МОНТАЖ",
        "visual": "набір кронштейнів, коробок і гермовводів на темному столі, готовий вузол камери",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Інструмент",
        "brand": "Монтажний набір",
        "product": "Тестер мережі + кримпер + витратні матеріали",
        "hook": "Професійний монтаж видно не по коробці, а по дрібницях.",
        "pain": "Неправильний обжим або неперевірена лінія дають плаваючі проблеми через тиждень.",
        "solution": "Перевіряємо кабелі, обжимаємо конектори й залишаємо систему охайною та сервісною.",
        "specs": ["LAN-тестер", "кримпер", "RJ45", "маркування кабелю"],
        "audience": "монтаж / сервіс / аудит системи",
        "keyword": "ТЕСТ",
        "visual": "молодий монтажник перевіряє лінію тестером, поруч інструменти й підписані кабелі",
        "source_url": "https://viatec.ua/ru",
    },
]


SERVICE_ANGLES = [
    {
        "topic": "Аудит системи",
        "brand": "ALT-CAM",
        "product": "Перевірка слабких місць відеонагляду",
        "hook": "Система ніби працює, але чи буде відео доказом?",
        "pain": "Неправильні кути, слабке нічне бачення, відсутній архів і поганий кабель часто виявляються після інциденту.",
        "solution": "Проводимо аудит, показуємо слабкі місця й даємо зрозумілий план доопрацювання.",
        "specs": ["перевірка кутів", "тест нічної картинки", "аналіз архіву", "рекомендації"],
        "audience": "будинок / бізнес / ОСББ / склад",
        "keyword": "АУДИТ",
        "visual": "Сергій дивиться на план об’єкта й монітори камер, червоні позначки проблемних зон",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Комплект під ключ",
        "brand": "ALT-CAM",
        "product": "Відеонагляд + Ajax + резервне живлення",
        "hook": "Безпека працює тільки тоді, коли всі елементи зібрані в одну систему.",
        "pain": "Окрема камера, окремий роутер і окрема сигналізація без сценарію часто не вирішують задачу.",
        "solution": "Проєктуємо комплекс: камери, сигналізацію, домофонію, мережу й резерв живлення.",
        "specs": ["проєктування", "обладнання", "монтаж", "налаштування застосунків"],
        "audience": "приватний будинок / бізнес / офіс",
        "keyword": "ПІД КЛЮЧ",
        "visual": "колаж системи: камера, Ajax, домофон, UPS, смартфон із застосунком",
        "source_url": "https://viatec.ua/ru",
    },
    {
        "topic": "Сервіс",
        "brand": "ALT-CAM",
        "product": "Обслуговування камер і систем безпеки",
        "hook": "Камера може працювати роками — якщо її не забути після монтажу.",
        "pain": "Пил, павутина, збитий фокус, старий пароль або переповнений диск знижують користь системи.",
        "solution": "Робимо сервіс: чистка, перевірка архіву, оновлення, тест доступу зі смартфона.",
        "specs": ["чистка камер", "перевірка HDD", "оновлення", "тест віддаленого доступу"],
        "audience": "магазин / офіс / будинок / склад",
        "keyword": "СЕРВІС",
        "visual": "монтажник чистить купольну камеру в офісі, поряд чек-лист сервісу",
        "source_url": "https://viatec.ua/ru",
    },
]


def ensure_dirs() -> None:
    for path in [
        OUT,
        OUT / "media" / "cards",
        OUT / "media" / "reels",
        OUT / "image-prompts",
        OUT / "brand-references",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def copy_references() -> list[dict]:
    refs = []
    for idx, src in enumerate(REFERENCE_IMAGES, start=1):
        if not src.exists():
            continue
        dst = OUT / "brand-references" / f"reference-{idx:02d}{src.suffix.lower()}"
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        refs.append({"label": f"reference-{idx:02d}", "path": dst.relative_to(OUT).as_posix()})
    return refs


def font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def wrap(draw, text: str, max_width: int, font_obj) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font_obj)
        if bbox[2] - bbox[0] <= max_width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_wrapped(draw, xy, text, max_width, font_obj, fill, line_spacing=8, max_lines=None) -> int:
    x, y = xy
    lines = wrap(draw, text, max_width, font_obj)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += font_obj.size + line_spacing
    return y


def pick_asset(item: dict, idx: int) -> Path | None:
    pool = ASSET_POOLS.get(item["topic"], [])
    available = []
    for entry in pool:
        repo_candidate = ROOT / entry
        local_candidate = LOCAL_ASSET_ROOT / entry
        if repo_candidate.exists():
            available.append(repo_candidate)
        elif local_candidate.exists():
            available.append(local_candidate)
    if not available:
        return None
    return available[idx % len(available)]


def pick_person(idx: int) -> Path | None:
    available = [entry for entry in PERSON_IMAGES if entry.exists()]
    if not available:
        return None
    return available[idx % len(available)]


def paste_cover(base, source, box, radius: int = 28, dim: float = 0.28, focus_y: float = 0.5) -> None:
    if Image is None:
        return
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    src = Image.open(source).convert("RGBA")
    ratio = max(bw / src.width, bh / src.height)
    src = src.resize((int(src.width * ratio), int(src.height * ratio)))
    left = (src.width - bw) // 2
    top = int(max(0, src.height - bh) * max(0, min(1, focus_y)))
    src = src.crop((left, top, left + bw, top + bh))
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 0, int(255 * dim)))
    src.alpha_composite(overlay)
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=radius, fill=255)
    base.paste(src, (x1, y1), mask)


def paste_contain(base, source, box, pad: int = 18) -> None:
    if Image is None:
        return
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1 - 2 * pad, y2 - y1 - 2 * pad
    src = Image.open(source).convert("RGBA")
    src.thumbnail((bw, bh), Image.LANCZOS)
    px = x1 + pad + (bw - src.width) // 2
    py = y1 + pad + (bh - src.height) // 2
    base.paste(src, (px, py), src)


def card_image(item: dict, path: Path, idx: int, format_9x16: bool = False) -> None:
    if Image is None:
        path.with_suffix(".txt").write_text(item["visual"], encoding="utf-8")
        return

    w, h = (1080, 1920) if format_9x16 else (1080, 1350)
    img = Image.new("RGB", (w, h), "#090909")
    draw = ImageDraw.Draw(img)

    # Premium dark gradient with yellow light streaks.
    for y in range(h):
        tone = int(14 + 28 * (y / h))
        draw.line((0, y, w, y), fill=(tone, tone, tone))
    draw.ellipse((-260, -170, 520, 380), fill=(38, 31, 7))
    draw.line((760, 0, 1180, h), fill=(245, 186, 0), width=8)
    draw.line((795, 0, 1215, h), fill=(58, 50, 18), width=4)

    margin = 58
    gold = "#ffcc00"
    white = "#f5f5f7"
    muted = "#b7b7bd"
    panel = "#141414"
    line = "#343434"

    draw.text((margin, 46), "ALT-CAM", font=font(60, True), fill=white)
    draw.text((margin + 5, 108), "SECURITY UA", font=font(28, True), fill=gold)

    y = 190
    draw.rectangle((margin, y, min(w - margin, margin + 520), y + 58), fill=gold)
    draw.text((margin + 22, y + 12), item["topic"].upper(), font=font(30, True), fill="#050505")
    y += 92

    headline = item["hook"].replace(" — ", "\n")
    y = draw_wrapped(draw, (margin, y), headline, w - 2 * margin, font(66, True), white, line_spacing=10, max_lines=4)
    y += 22
    y = draw_wrapped(draw, (margin, y), f"{item['brand']} {item['product']}", w - 2 * margin, font(38, True), gold, line_spacing=8, max_lines=2)

    # Product/person visual panel. Person is intentionally large enough for face + torso/body visibility.
    hero_top = 555 if not format_9x16 else 660
    draw.rounded_rectangle((margin, hero_top, w - margin, hero_top + 310), radius=32, fill=panel, outline=line, width=2)
    asset = pick_asset(item, idx)
    person = pick_person(idx)
    visual_box = (w - 520, hero_top + 18, w - margin - 18, hero_top + 292)
    if person:
        paste_cover(img, person, visual_box, radius=30, dim=0.03, focus_y=0.08)
        draw.rounded_rectangle(visual_box, radius=30, outline=gold, width=3)
        if asset and "marketing-scenes" not in asset.as_posix() and "grok-video-source" not in asset.as_posix():
            product_box = (visual_box[0] + 238, visual_box[1] + 148, visual_box[2] - 12, visual_box[3] - 12)
            draw.rounded_rectangle(product_box, radius=22, fill="#f6f6f6", outline=gold, width=2)
            paste_contain(img, asset, product_box, pad=16)
    elif asset:
        if "marketing-scenes" in asset.as_posix() or "grok-video-source" in asset.as_posix():
            paste_cover(img, asset, visual_box, radius=30, dim=0.08)
        else:
            draw.rounded_rectangle(visual_box, radius=30, fill="#f6f6f6", outline=gold, width=2)
            paste_contain(img, asset, visual_box, pad=24)
    else:
        draw.rounded_rectangle(visual_box, radius=30, fill="#242424", outline=gold, width=3)
        draw.text((visual_box[0] + 42, visual_box[1] + 98), item["keyword"], font=font(36, True), fill=gold)
    draw.text((margin + 32, hero_top + 28), "ПЕРСОНАЖ + ТОВАР", font=font(28, True), fill=gold)
    draw_wrapped(draw, (margin + 32, hero_top + 78), item["visual"], visual_box[0] - margin - 62, font(29, False), white, line_spacing=7, max_lines=5)
    draw.rounded_rectangle((visual_box[0] + 26, visual_box[3] - 45, visual_box[2] - 26, visual_box[3] - 12), radius=15, fill=(0, 0, 0))
    draw.text((visual_box[0] + 48, visual_box[3] - 40), item["keyword"], font=font(21, True), fill=gold)

    specs_top = hero_top + 360
    spec_h = 118
    cols = 2
    col_w = (w - 2 * margin - 18) // cols
    for n, spec in enumerate(item["specs"][:6]):
        x = margin + (n % cols) * (col_w + 18)
        yy = specs_top + (n // cols) * (spec_h + 18)
        draw.rounded_rectangle((x, yy, x + col_w, yy + spec_h), radius=20, fill="#101010", outline="#3a3212", width=2)
        draw.ellipse((x + 28, yy + 40, x + 48, yy + 60), fill=gold)
        draw_wrapped(draw, (x + 78, yy + 27), spec, col_w - 100, font(27, True), white, line_spacing=5, max_lines=2)

    cta_y = h - 180
    draw.rounded_rectangle((margin, cta_y, w - margin, cta_y + 92), radius=24, fill=gold)
    draw.text((margin + 34, cta_y + 22), f"ПИШІТЬ «{item['keyword']}» У ПОВІДОМЛЕННЯ", font=font(32, True), fill="#060606")
    draw.text((margin, h - 62), "Офіційне обладнання • акуратний монтаж • Київ та область", font=font(25, True), fill=muted)

    img.save(path, quality=92)


def caption_common(item: dict) -> str:
    return (
        f"{item['hook']}\n\n"
        f"Проблема: {item['pain']}\n\n"
        f"Рішення ALT-CAM: {item['solution']}\n\n"
        f"{item['brand']} {item['product']}\n"
        + "\n".join(f"• {s}" for s in item["specs"])
        + f"\n\nДля кого: {item['audience']}.\n\n"
        f"Напишіть «{item['keyword']}» — підберемо варіант під ваш об’єкт, бюджет і монтаж.\n"
        f"{BOT_URL}\n{SITE_URL}"
    )


def captions(item: dict) -> dict:
    hashtags = " ".join(HASHTAGS_BASE + [f"#{item['keyword'].lower().replace(' ', '')}", "#системибезпеки"])
    common = caption_common(item)
    telegram = (
        f"<b>{item['hook']}</b>\n\n"
        f"<b>Проблема:</b> {item['pain']}\n\n"
        f"<b>Рішення ALT-CAM:</b> {item['solution']}\n\n"
        f"<b>{item['brand']} {item['product']}</b>\n"
        + "\n".join(f"• {s}" for s in item["specs"])
        + f"\n\n<code>Ціну та комплектацію підбираємо під об’єкт, монтаж і сценарій роботи.</code>\n\n"
        f"Напишіть «{item['keyword']}» — підберемо рішення.\n{BOT_URL}"
    )
    return {
        "facebook": f"{common}\n\n{hashtags}",
        "instagram": f"{common}\n\nЗбережіть пост, щоб не загубити підбір.\n\n{hashtags}",
        "threads": f"{item['hook']} {item['solution']} Напишіть «{item['keyword']}» — підберемо рішення під об’єкт. {BOT_URL}",
        "telegram": telegram,
        "youtube": f"{item['hook']}\nКороткий розбір: {item['solution']}\nДеталі та підбір: {BOT_URL}",
    }


def media_prompt(item: dict, day_num: int, post_num: int) -> str:
    return dedent(f"""
    Створи преміальну вертикальну рекламну картку ALT-CAM Security UA у стилі наданих референсів.

    Формат:
    - 1080×1350 для Instagram/Facebook або 1080×1920 для Stories/Reels cover.
    - Темний графітовий фон, жовті акценти, чиста преміальна типографіка.
    - Не згадувати постачальників і сайти постачальників.

    Сцена:
    - Тема: {item['topic']}.
    - Товар/рішення: {item['brand']} {item['product']}.
    - Візуал: {item['visual']}.
    - Чергувати живі елементи: Сергій/Аліса/молодий монтажник/реальний об’єкт/товар на столі.

    Текст на картці:
    1. Великий заголовок: «{item['hook']}»
    2. Плашка: «{item['keyword']}»
    3. Блок характеристик:
       - {'; '.join(item['specs'])}
    4. CTA: «Напишіть “{item['keyword']}” — підберемо рішення»

    Композиція:
    - Великий товар або людина з товаром займає 45–55% кадру.
    - Характеристики в нижній сітці з іконками.
    - Логотип ALT-CAM зверху ліворуч, без помилок у тексті.
    - Вигляд має бути як професійна реклама систем безпеки, не як шаблонна стокова картинка.
    """).strip()


def slug(value: str) -> str:
    mapping = {
        "РЕЗЕРВ": "reserve",
        "НАПРУГА": "voltage",
        "АВТОНОМІЯ": "autonomy",
        "КОЛІР ВНОЧІ": "color-night",
        "ПЕРИМЕТР": "perimeter",
        "PTZ": "ptz",
        "ДОМОФОН": "intercom",
        "ВХІД": "entrance",
        "ДОСТУП": "access",
        "AJAX": "ajax",
        "АРХІВ": "archive",
        "PoE": "poe",
        "КАБЕЛЬ": "cable",
        "МОНТАЖ": "mounting",
        "ТЕСТ": "test",
        "АУДИТ": "audit",
        "ПІД КЛЮЧ": "turnkey",
        "СЕРВІС": "service",
    }
    return mapping.get(value, "post").lower().replace(" ", "-")


def reel_post(day: date, items: list[dict], day_index: int) -> dict:
    subject = items[0]
    title = f"Що буде, якщо зекономити на темі «{subject['topic']}»?"
    scenario = {
        "0-3s": f"Крупний план проблеми: {subject['pain']} На екрані великий текст: «СТОП. Це слабке місце?»",
        "3-12s": f"Показати, як проблема виглядає на реальному об’єкті: темний двір, щит, двері або камера без деталей.",
        "12-22s": f"Контраст: охайне рішення ALT-CAM — {subject['brand']} {subject['product']}, налаштування, перевірка зі смартфона.",
        "22-30s": f"Вердикт: «Безпека — це система, а не одна коробка». CTA: «Пишіть “{subject['keyword']}” у Telegram-бот».",
    }
    prompt = dedent(f"""
    Reels/TikTok/Shorts cover у стилі ALT-CAM:
    - Кадр 1: проблема й емоція, людина помічає збій або небезпеку.
    - Кадр 2: як могло бути у сусіда / правильний сценарій.
    - Кадр 3: рішення ALT-CAM з товаром {subject['brand']} {subject['product']}.
    - Кадр 4: вердикт + CTA до Telegram-бота.
    Стиль: темний преміальний, жовті акценти, живі люди, реальний об’єкт, без згадки постачальників.
    """).strip()
    media_name = f"reel_day_{day_index:02d}_cover.png"
    media_path = OUT / "media" / "reels" / media_name
    cover_item = {**subject, "hook": title, "visual": "динамічна заставка: проблема → рішення → вердикт → CTA"}
    card_image(cover_item, media_path, day_index, format_9x16=True)
    return {
        "id": f"sep10d-{day_index:02d}-reel",
        "type": "reel_carousel",
        "scheduled_at": datetime.combine(day, time(20, 30), TZ).isoformat(),
        "platforms": ["instagram_reels", "facebook_reels", "tiktok", "youtube_shorts", "telegram"],
        "title": title,
        "media_type": "image",
        "media_path": media_path.relative_to(OUT).as_posix(),
        "media_status": "draft_cover_generated",
        "scenario": scenario,
        "carousel_slides": [
            "Слайд 1: проблема, яка коштує грошей або спокою",
            "Слайд 2: як це виглядає на реальному об’єкті",
            "Слайд 3: рішення ALT-CAM",
            "Слайд 4: вердикт і CTA в Telegram-бот",
        ],
        "caption": f"{title}\n\n{subject['solution']}\n\nНапишіть «{subject['keyword']}» у Telegram-бот — підберемо рішення під ваш об’єкт.\n{BOT_URL}\n\n{' '.join(HASHTAGS_BASE + ['#reelsукраїна', '#tiktokукраїна'])}",
        "image_prompt": prompt,
    }


def build_posts() -> list[dict]:
    items = PRODUCTS + SERVICE_ANGLES
    start = date(2026, 9, 10)
    schedule_times = [time(10, 0), time(14, 0), time(18, 0)]
    posts: list[dict] = []
    item_index = 0
    for day_index in range(1, 11):
        current = start + timedelta(days=day_index - 1)
        day_items = []
        for slot_index, slot_time in enumerate(schedule_times, start=1):
            item = items[item_index % len(items)]
            item_index += 1
            day_items.append(item)
            post_id = f"sep10d-{day_index:02d}-{slot_index:02d}"
            media_name = f"{post_id}-{slug(item['keyword'])}.png"
            media_path = OUT / "media" / "cards" / media_name
            card_image(item, media_path, item_index)
            prompt_text = media_prompt(item, day_index, slot_index)
            prompt_path = OUT / "image-prompts" / f"{post_id}.md"
            prompt_path.write_text(prompt_text, encoding="utf-8")
            posts.append(
                {
                    "id": post_id,
                    "type": "product_card",
                    "scheduled_at": datetime.combine(current, slot_time, TZ).isoformat(),
                    "platforms": ["facebook", "instagram", "threads", "telegram"],
                    "title": item["hook"],
                    "topic": item["topic"],
                    "product": item,
                    "captions": captions(item),
                    "hashtags": HASHTAGS_BASE + [f"#{item['keyword'].lower().replace(' ', '')}", "#системибезпеки"],
                    "media_type": "image",
                    "media_path": media_path.relative_to(OUT).as_posix(),
                    "media_status": "draft_card_generated",
                    "image_prompt_path": prompt_path.relative_to(OUT).as_posix(),
                    "image_prompt": prompt_text,
                }
            )
        posts.append(reel_post(current, day_items, day_index))
    posts.sort(key=lambda p: p["scheduled_at"])
    ai_first = OUT / "media" / "ai-final" / "sep10d-01-01-reserve-ai-final.png"
    if ai_first.exists() and posts:
        posts[0]["ai_media_path"] = ai_first.relative_to(OUT).as_posix()
        posts[0]["preferred_media_path"] = posts[0]["ai_media_path"]
        posts[0]["media_status"] = "ai_final_ready"
    return posts


def write_calendar(posts: list[dict], references: list[dict]) -> None:
    data = {
        "plan_id": PLAN_ID,
        "title": "ALT-CAM: 10 днів нових товарних публікацій",
        "period": "10–19 вересня 2026",
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "notes": [
            "Публічні тексти не містять назв постачальників або посилань на сайти постачальників.",
            "Для Telegram залишено HTML тільки у полі telegram; інші соцмережі без HTML-тегів.",
            "Медіа-картки згенеровані як чорнові обкладинки + окремі промти для фінальної генерації в стилі референсів.",
        ],
        "references": references,
        "posts": posts,
    }
    CALENDAR_DATA.write_text(
        "window.ALT_CAM_SEP_10_DAY_PRODUCT_POSTS = "
        + json.dumps(data, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    html = """<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ALT-CAM: 10 днів товарних публікацій</title>
  <style>
    :root{color-scheme:dark;--bg:#111113;--panel:rgba(255,255,255,.045);--line:rgba(255,255,255,.12);--text:#F5F5F7;--muted:#9A9AA0;--gold:#FFCC00}
    *{box-sizing:border-box} body{margin:0;font-family:Inter,system-ui,Segoe UI,sans-serif;background:radial-gradient(circle at top left,rgba(255,204,0,.16),transparent 34rem),var(--bg);color:var(--text)}
    main{width:min(1240px,calc(100% - 28px));margin:0 auto;padding:38px 0 70px}
    header{display:grid;grid-template-columns:1fr auto;gap:22px;align-items:end;margin-bottom:22px} h1{font-size:clamp(32px,5vw,58px);line-height:.96;margin:0 0 10px;letter-spacing:-.045em} p{color:var(--muted);line-height:1.55;margin:0}
    .badge,.chip,a.chip{border:1px solid var(--line);background:var(--panel);border-radius:999px;padding:8px 12px;color:var(--text);text-decoration:none;display:inline-flex;gap:6px;align-items:center;font-size:13px}
    .toolbar,.ref-grid{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.ref-grid img{width:140px;height:180px;object-fit:cover;border-radius:18px;border:1px solid var(--line)}
    .grid{display:grid;gap:18px}.day{border:1px solid var(--line);border-radius:24px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.025))}
    .day-head{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;background:rgba(255,255,255,.035)} h2{font-size:20px;margin:0}
    .post{display:grid;grid-template-columns:86px 210px 1fr;gap:18px;padding:18px 20px;border-bottom:1px solid var(--line)}.post:last-child{border-bottom:0}.time{color:var(--gold);font-weight:900;font-size:18px}
    img.media{width:210px;aspect-ratio:4/5;object-fit:cover;border-radius:18px;border:1px solid var(--line);background:#222} img.media.vertical{aspect-ratio:9/16}
    h3{margin:0 0 8px;font-size:21px}.meta{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.gold{color:var(--gold)}
    details{margin-top:10px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:rgba(0,0,0,.2)}summary{cursor:pointer;padding:12px 14px;color:var(--gold);font-weight:800}pre{white-space:pre-wrap;margin:0;padding:0 14px 14px;font-family:inherit;line-height:1.5;color:#ddd}
    @media(max-width:760px){header{display:block}.post{grid-template-columns:1fr}.time{font-size:22px}img.media{width:100%;max-height:520px}.ref-grid img{width:30%;height:auto}}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>ALT-CAM: 10 днів нових публікацій</h1>
      <p>3 товарно-сервісні пости щодня + 1 Reels/TikTok/Shorts. Стиль: преміальна темна картка, живі люди, товар, монтаж у роботі, реальні болі клієнта.</p>
    </div>
    <div class="badge">10–19 вересня 2026</div>
  </header>
  <nav class="toolbar">
    <a class="chip" href="./product-week.html">попередній товарний календар</a>
    <a class="chip" href="../content-plans/2026-09-10-10-day-product-presentation/PLAN.md">PLAN.md</a>
    <a class="chip" href="../content-plans/2026-09-10-10-day-product-presentation/publishing-posts.json">publishing-posts.json</a>
    <a class="chip" href="../content-plans/2026-09-10-10-day-product-presentation/image-prompts/">промти для медіа</a>
  </nav>
  <section id="refs" class="ref-grid"></section>
  <section id="calendar" class="grid"></section>
</main>
<script src="./sep-10-day-product-posts-data.js"></script>
<script>
const data = window.ALT_CAM_SEP_10_DAY_PRODUCT_POSTS;
const calendar = document.getElementById('calendar');
const refs = document.getElementById('refs');
const fmtDate = new Intl.DateTimeFormat('uk-UA',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Kyiv'});
const fmtTime = new Intl.DateTimeFormat('uk-UA',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Kyiv'});
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function block(label,text){return `<details><summary>${esc(label)}</summary><pre>${esc(text)}</pre></details>`}
refs.innerHTML = data.references.map(r=>`<img src="../content-plans/${data.plan_id}/${r.path}" alt="${esc(r.label)}">`).join('');
const days = new Map();
for(const post of data.posts){const key=post.scheduled_at.slice(0,10); if(!days.has(key)) days.set(key,[]); days.get(key).push(post);}
calendar.innerHTML = [...days.entries()].map(([key,posts])=>`
  <article class="day">
    <div class="day-head"><h2>${fmtDate.format(new Date(posts[0].scheduled_at))}</h2><span class="badge">${posts.length} публікації</span></div>
    ${posts.map(post=>{
      const vertical = post.type === 'reel_carousel';
      const media = `../content-plans/${data.plan_id}/${post.preferred_media_path || post.media_path}`;
      const captions = post.type === 'product_card'
        ? block('Facebook', post.captions.facebook) + block('Instagram', post.captions.instagram) + block('Threads', post.captions.threads) + block('Telegram', post.captions.telegram) + block('YouTube Community', post.captions.youtube) + block('Промт для фінального медіа', post.image_prompt)
        : block('Сценарій Reels/TikTok/Shorts', Object.entries(post.scenario).map(([k,v])=>`${k}: ${v}`).join('\\n')) + block('Карусель', post.carousel_slides.join('\\n')) + block('Caption', post.caption) + block('Промт для обкладинки/кадрів', post.image_prompt);
      return `<div class="post">
        <div class="time">${fmtTime.format(new Date(post.scheduled_at))}</div>
        <img class="media ${vertical?'vertical':''}" src="${media}" alt="${esc(post.title)}">
        <div>
          <h3>${esc(post.title)}</h3>
          <p><span class="gold">${esc(post.topic || 'Reels')}</span>${post.product ? ' · '+esc(post.product.brand+' '+post.product.product) : ''}</p>
          <div class="meta">${post.platforms.map(p=>`<span class="chip">${esc(p)}</span>`).join('')}<span class="chip">${esc(post.media_status)}</span></div>
          ${captions}
        </div>
      </div>`;
    }).join('')}
  </article>`).join('');
</script>
</body>
</html>
"""
    CALENDAR_HTML.write_text(html, encoding="utf-8")


def write_plan(posts: list[dict], references: list[dict]) -> None:
    publishing = {
        "plan_id": PLAN_ID,
        "period": "2026-09-10/2026-09-19",
        "cta": {"bot": BOT_URL, "site": SITE_URL},
        "posts": posts,
    }
    (OUT / "publishing-posts.json").write_text(json.dumps(publishing, ensure_ascii=False, indent=2), encoding="utf-8")

    by_day: dict[str, list[dict]] = {}
    for post in posts:
        by_day.setdefault(post["scheduled_at"][:10], []).append(post)

    lines = [
        "# ALT-CAM Security UA — 10 днів нових публікацій",
        "",
        "Період: **10–19 вересня 2026**.",
        "",
        "Формат: щодня 3 товарно-сервісні пости + 1 Reels/TikTok/Shorts. Публічні тексти не містять згадок постачальників або посилань на сайти постачальників.",
        "",
        "## Бренд-референси",
        "",
    ]
    for ref in references:
        lines.append(f"- `{ref['path']}`")
    lines.extend(["", "## Публікації", ""])
    for day, day_posts in by_day.items():
        lines.append(f"### {day}")
        lines.append("")
        for post in day_posts:
            lines.append(f"- **{post['scheduled_at'][11:16]}** — {post['title']} (`{post['type']}`)")
            lines.append(f"  - Платформи: {', '.join(post['platforms'])}")
            lines.append(f"  - Медіа: `{post['media_path']}`")
            if post.get("image_prompt_path"):
                lines.append(f"  - Промт: `{post['image_prompt_path']}`")
        lines.append("")
    (OUT / "PLAN.md").write_text("\n".join(lines), encoding="utf-8")

    ready_lines = [
        "# Готові пости ALT-CAM — картинки, назви, описи, хештеги",
        "",
        "Період: **10–19 вересня 2026**. Публічні тексти не містять згадок постачальників.",
        "",
    ]
    for post in posts:
        title = post["title"]
        media = post.get("preferred_media_path") or post["media_path"]
        ready_lines.extend(
            [
                f"## {post['scheduled_at'][:10]} {post['scheduled_at'][11:16]} — {title}",
                "",
                f"**Картинка:** `{media}`",
                "",
                f"**Платформи:** {', '.join(post['platforms'])}",
                "",
            ]
        )
        if post["type"] == "product_card":
            ready_lines.extend(
                [
                    "### Назва",
                    "",
                    title,
                    "",
                    "### Опис для Instagram / Facebook",
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
                    "### Хештеги",
                    "",
                    " ".join(post["hashtags"]),
                    "",
                ]
            )
        else:
            ready_lines.extend(
                [
                    "### Назва",
                    "",
                    title,
                    "",
                    "### Опис",
                    "",
                    post["caption"],
                    "",
                    "### Сценарій",
                    "",
                    "\n".join(f"- **{k}:** {v}" for k, v in post["scenario"].items()),
                    "",
                ]
            )
    (OUT / "READY_POSTS.md").write_text("\n".join(ready_lines), encoding="utf-8")


def validate(posts: list[dict]) -> dict:
    errors = []
    public_fields = []
    for post in posts:
        if post["type"] == "product_card":
            for key in ["facebook", "instagram", "threads", "youtube"]:
                public_fields.append((post["id"], key, post["captions"][key]))
        else:
            public_fields.append((post["id"], "caption", post["caption"]))
    for post_id, field, text in public_fields:
        lowered = text.lower()
        if "viatec" in lowered or "neolight" in lowered or "yugtorg" in lowered:
            errors.append(f"{post_id}:{field}: supplier mention")
        if "<b>" in text or "</b>" in text or "<code>" in text or "</code>" in text:
            errors.append(f"{post_id}:{field}: html tag in public caption")
        if "t.me/altcam_security_ua" in text:
            errors.append(f"{post_id}:{field}: unwanted channel link")
    missing_media = [p["id"] for p in posts if not (OUT / p["media_path"]).exists()]
    if missing_media:
        errors.append(f"missing media: {missing_media[:5]}")
    return {
        "posts": len(posts),
        "days": len({p["scheduled_at"][:10] for p in posts}),
        "errors": errors,
    }


def main() -> None:
    ensure_dirs()
    references = copy_references()
    posts = build_posts()
    write_calendar(posts, references)
    write_plan(posts, references)
    report = validate(posts)
    (OUT / "validation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if report["errors"]:
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
