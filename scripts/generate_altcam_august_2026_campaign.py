from __future__ import annotations

import json
import math
import re
import textwrap
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / "social-posts" / "calendar"
MEDIA = ROOT / "social-posts" / "august-2026-media"
DATA = CALENDAR / "altcam-august-2026-data.js"
INDEX = CALENDAR / "index.html"
QUEUE = ROOT / "social-posts" / "weekly-automation" / "posts.json"
CHARACTERS = [
    ROOT / "social-posts" / "characters" / "character-2-founder-altcam-uniform.png",
    ROOT / "social-posts" / "characters" / "character-1-woman-altcam-uniform.png",
]
PRODUCT_ROOT = ROOT / "social-posts" / "instagram-catalog" / "product-photos"
LOGO = ROOT / "social-posts" / "brand-assets" / "grok-video-source" / "16-altcam-full-logo-source.png"
BOT = "https://t.me/altcam_security_ua"
SITE = "https://alt-cam.net.ua"
LOCATION = "Київ • Вишгород • Київська область"
HASHTAGS = "#AltCam #відеоспостереженнякиїв #монтажкамер #системибезпеки #Київ #Вишгород"
FONT_BOLD = Path("C:/Windows/Fonts/seguisb.ttf")
FONT_REGULAR = Path("C:/Windows/Fonts/segoeui.ttf")


SOURCES = [
    "https://viatec.ua/",
    "https://nadzor.ua/uk",
    "https://www.instagram.com/yugtorgcom/",
]

TOPICS = [
    ("Чому камера не бачить обличчя вночі", "Камера є, а доказів немає?", "Hikvision / Dahua", "Перевіряємо висоту, кут, засвіт, об'єктив та нічний режим."),
    ("ColorVu, WizColor і звичайне ІЧ", "Колір уночі чи непомітне ІЧ?", "Hikvision / Dahua", "Пояснюємо різницю та підбираємо технологію під реальне освітлення."),
    ("AcuSense та WizSense", "Камера відрізнить людину від гілки?", "Hikvision / Dahua", "Розумна фільтрація зменшує зайві сповіщення від тварин, дощу та листя."),
    ("Кібербезпека IP-камер", "Хто ще має доступ до ваших камер?", "Hikvision / Dahua / Uniview", "Окремі акаунти, складні паролі, 2FA, оновлення та контроль користувачів."),
    ("Автономна камера 4G", "Немає кабелю та Wi-Fi — камери не буде?", "Imou / Dahua", "4G, акумулятор і сонячна панель дозволяють контролювати віддалені об'єкти."),
    ("Архів відеоспостереження", "Запис є, але потрібний день уже стерся?", "Hikvision / Dahua", "Рахуємо HDD за кількістю камер, бітрейтом і потрібною глибиною архіву."),
    ("Резервне живлення", "Світло зникло — безпека теж?", "UPS / LiFePO4 / Ajax", "Резервуємо камери, NVR, PoE, роутер, ONU та охоронну систему як один ланцюг."),
    ("IP-домофон зі смартфоном", "Хто біля хвіртки, коли вас немає вдома?", "Dahua / Hikvision", "Виклик, відео та відкриття дверей зі смартфона з контрольованими правами."),
    ("Ajax і відеоперевірка", "Тривога є — а що саме сталося?", "Ajax / Hikvision / Dahua", "Поєднуємо датчики, камери, сирену, сценарії та резервне живлення."),
    ("СКУД для офісу", "Хто досі має ключ від вашого офісу?", "U-Prox / Dahua / Hikvision", "Картки, коди, журнал подій і швидке блокування доступу без заміни замків."),
    ("Камери для магазину", "Каса в кадрі, але операцію не видно?", "Hikvision / Dahua / Uniview", "Проєктуємо окремі ракурси для входу, каси, залу, складу та архіву."),
    ("Монтаж без хаосу", "Кабелі висять, а підписів немає?", "ALT-CAM", "Маркуємо лінії, збираємо щит, тестуємо архів, нічну картинку та доступ."),
    ("Wi-Fi камера за бетонними стінами", "Чому камера постійно зникає з мережі?", "Imou / Hikvision / Dahua", "Перевіряємо сигнал, частоти та навантаження; для критичних зон радимо кабель."),
    ("PTZ чи кілька фіксованих камер", "Одна поворотна камера замінить чотири?", "Dahua / Hikvision", "Порівнюємо постійне покриття, деталізацію, патрулювання та ризик сліпих зон."),
    ("Оновлення аналогової системи", "Треба міняти всі кабелі для кращої картинки?", "Hikvision / Dahua", "Іноді достатньо XVR і нових камер; рішення приймаємо після аудиту трас."),
]

PRODUCTS = [
    ("Dahua DH-HAC-T1A21P 2 Мп", "Купольна камера для базових внутрішніх зон", "від 662 ₴", "Кут до 103°, ІЧ до 20 м", "https://nadzor.ua/uk/akcii"),
    ("Dahua DH-HAC-B2A51 5 Мп", "Вулична HDCVI-камера з деталізацією 5 Мп", "від 1 012 ₴", "Об'єктив 2.8 мм, IP67, ІЧ до 20 м", "https://nadzor.ua/uk/akcii"),
    ("Dahua DH-IPC-HFW1320SP-W 3 Мп", "Wi-Fi/LAN камера для дому або малого бізнесу", "від 2 520 ₴", "MicroSD, IP67, підсвічування до 30 м", "https://nadzor.ua/uk/akcii"),
    ("Dahua DH-IPC-HDBW2249E-S-IL 2 Мп", "IP-камера з мікрофоном та комбінованим світлом", "від 3 465 ₴", "PoE, мікрофон, інтелектуальне підсвічування", "https://viatec.ua/product/nabir-podarunkovii-hikvision"),
    ("Hikvision DS-2CD1047G3-LIUF 4 Мп", "Кольорова нічна картинка для важливих зон", "від 5 947 ₴", "4 Мп, вуличне виконання, сучасна нічна технологія", "https://nadzor.ua/uk/videonablyudenie/komplekty-videonabludenia/dahua-komplekty-videonabludenia"),
    ("Hikvision iDS-7108HQHI-M1/S(E)", "8-канальний XVR з AcuSense", "від 6 525 ₴", "Гібридні камери, інтелектуальна фільтрація", "https://viatec.ua/product/hikvision-s-paket"),
    ("Ajax NVR HAC 8ch", "Відеореєстратор у застосунку Ajax", "від 7 599 ₴", "До 8 каналів, єдина екосистема безпеки", "https://viatec.ua/product/hikvision-s-paket"),
    ("Ajax SpeakerPhone", "Голосовий модуль для перевірки тривог", "від 6 099 ₴", "Двосторонній голосовий зв'язок в екосистемі Ajax", "https://viatec.ua/product/hikvision-s-paket"),
    ("Dahua DHI-VTH2421FW-P", "7-дюймовий IP-відеодомофон", "від 6 480 ₴", "PoE, сенсорний екран, інтеграція з викличною панеллю", "https://viatec.ua/product/nabir-podarunkovii-hikvision"),
    ("Dahua PT 4G 3+3 Мп", "Поворотна автономна камера для віддалених об'єктів", "від 15 750 ₴", "Два об'єктиви, 4G, поворотний механізм", "https://viatec.ua/product/hikvision-s-paket"),
    ("Dahua PTZ X-Spans 4+4 Мп", "Панорама плюс 25-кратний оптичний зум", "від 29 475 ₴", "PTZ 25× і панорамний канал 101°", "https://viatec.ua/product/hikvision-s-paket"),
]

SERVICES = [
    ("Аудит системи безпеки", "Перевіримо сліпі зони, архів, доступ і резерв", "від 1 500 ₴"),
    ("Монтаж IP-камер", "Проєктування, кабель, монтаж, налаштування та навчання", "від 2 500 ₴/камера"),
    ("Налаштування смартфона", "Hik-Connect, DMSS або Imou Life з окремими правами", "від 1 200 ₴"),
    ("Монтаж IP-домофона", "Панель, монітор, замок, мобільний доступ і резерв", "від 6 900 ₴"),
    ("Резервне живлення", "Розрахунок автономності для камер, мережі та Ajax", "від 8 900 ₴"),
    ("СКУД під ключ", "Контролер, зчитувач, замок, БЖ і журнал подій", "від 12 900 ₴"),
    ("Модернізація старої системи", "Аудит кабелів, заміна XVR/NVR і камер без зайвих робіт", "від 3 900 ₴"),
]

SLOTS = [
    ("08:00", "Стаття", 1, ["facebook", "telegram", "youtube"], "16:9"),
    ("09:15", "Reels", 1, ["instagram", "facebook", "tiktok", "youtube_shorts"], "9:16"),
    ("10:30", "Пост", 1, ["instagram", "facebook", "telegram"], "4:5"),
    ("11:45", "Обговорення", 1, ["threads", "facebook", "telegram"], "16:9"),
    ("13:00", "Товар", 1, ["instagram", "facebook", "telegram", "tiktok"], "4:5"),
    ("14:15", "Стаття", 2, ["facebook", "telegram", "youtube"], "16:9"),
    ("15:30", "Reels", 2, ["instagram", "facebook", "tiktok", "youtube_shorts"], "9:16"),
    ("16:45", "Пост", 2, ["instagram", "facebook", "telegram"], "4:5"),
    ("18:00", "Обговорення", 2, ["threads", "facebook", "telegram"], "16:9"),
    ("19:15", "Товар", 2, ["instagram", "facebook", "telegram", "tiktok"], "4:5"),
    ("20:30", "Послуга", 1, ["facebook", "instagram", "threads", "telegram"], "4:5"),
]

COLORS = [(255, 204, 0), (45, 189, 255), (255, 112, 87), (64, 214, 143), (174, 112, 255)]

PUBLISH_DISTRIBUTION = {
    "Стаття": ["facebook", "telegram"],
    "Reels": ["instagram", "tiktok"],
    "Пост": ["instagram", "facebook", "telegram"],
    "Обговорення": ["threads", "facebook", "telegram"],
    "Товар": ["instagram", "facebook", "telegram", "tiktok"],
    "Послуга": ["facebook", "instagram", "threads", "telegram"],
}


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def source_images() -> dict[str, list[Path]]:
    groups = {}
    for category in ("cameras", "recorders", "intercoms", "ajax", "backup"):
        result = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            result.extend((PRODUCT_ROOT / category).glob(ext))
        groups[category] = sorted(result)
    groups["all"] = [path for values in groups.values() for path in values]
    return groups


def bright_canvas(size, accent):
    """Bright brand background without dimming the source photo."""
    w, h = size
    image = Image.new("RGB", size, (248, 249, 252))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((-w // 5, -h // 7, int(w * .72), int(h * .34)), radius=90, fill=accent)
    draw.ellipse((int(w * .70), int(h * .02), int(w * 1.18), int(h * .34)), fill=(255, 225, 92))
    draw.rectangle((0, h - 18, w, h), fill=accent)
    return image


def render_card(post: dict, background_path: Path, output: Path, slide=1, total=1):
    sizes = {"9:16": (1080, 1920), "4:5": (1080, 1350), "16:9": (1200, 630)}
    size = sizes[post["aspect_ratio"]]
    accent = COLORS[(post["day"] + post["slot_index"]) % len(COLORS)]
    canvas = bright_canvas(size, accent)
    bg = Image.open(background_path).convert("RGB")
    bg = ImageEnhance.Contrast(bg).enhance(1.03)
    bg = ImageEnhance.Color(bg).enhance(1.06)
    w, h = size
    if post["aspect_ratio"] == "16:9":
        photo_box = (int(w * .54), 34, w - 34, h - 34)
        text_width, x, y = int(w * .46), 54, 54
        title_size, small_size = 48, 23
    else:
        photo_top = int(h * .46)
        photo_box = (48, photo_top, w - 48, h - 178)
        text_width, x, y = w - 112, 56, 70
        title_size, small_size = (64 if post["aspect_ratio"] == "9:16" else 54), 27

    px0, py0, px1, py1 = photo_box
    canvas_draw = ImageDraw.Draw(canvas)
    canvas_draw.rounded_rectangle(photo_box, radius=38, fill=(255, 255, 255), outline=(220, 224, 232), width=3)
    fitted = ImageOps.contain(bg, (px1 - px0 - 24, py1 - py0 - 24), method=Image.Resampling.LANCZOS)
    fx = px0 + (px1 - px0 - fitted.width) // 2
    fy = py0 + (py1 - py0 - fitted.height) // 2
    canvas.paste(fitted, (fx, fy))
    canvas = canvas.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    label = post["content_format"].upper()
    if total > 1:
        label += f"  {slide}/{total}"
    draw.rounded_rectangle((x, y, x + 290, y + 48), radius=24, fill=(20, 24, 31, 255))
    draw.text((x + 20, y + 10), label, font=font(21, True), fill=accent)
    y += 78
    title_font = font(title_size, True)
    slide_titles = post.get("carousel_titles") or [post["question"]]
    title = slide_titles[min(slide - 1, len(slide_titles) - 1)]
    lines = wrap(draw, title, title_font, text_width)
    for line in lines[:4]:
        draw.text((x, y), line, font=title_font, fill=(15, 20, 29))
        y += title_size * 1.08
    draw.line((x, y + 14, x + min(300, text_width), y + 14), fill=accent, width=8)
    if post["content_format"] in {"Товар", "Послуга"}:
        info_font = font(25 if post["aspect_ratio"] != "16:9" else 22, False)
        info_y = y + 34
        for info_line in wrap(draw, post["summary"], info_font, text_width)[:3]:
            draw.text((x, info_y), info_line, font=info_font, fill=(42, 49, 60))
            info_y += 34
    bottom_y = h - (136 if post["aspect_ratio"] == "16:9" else 150)
    provider = "ПРОДАЄ ALT-CAM" if post["content_format"] == "Товар" else "НАДАЄ ALT-CAM" if post["content_format"] == "Послуга" else "ALT-CAM SECURITY UA"
    draw.text((x, bottom_y), provider, font=font(small_size, True), fill=(17, 22, 30))
    detail = post.get("price") if post["content_format"] in {"Товар", "Послуга"} else post["cta_short"]
    draw.text((x, bottom_y + 38), detail or post["cta_short"], font=font(small_size, True), fill=(17, 22, 30))
    draw.text((x, bottom_y + 76), "Київ • Вишгород • область", font=font(21), fill=(55, 62, 73))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, "JPEG", quality=78, optimize=True, progressive=True)


def base_caption(title, question, body, price=None):
    money = f"\n\n💰 {price}" if price else ""
    return (
        f"{question}\n\n{title}. {body}{money}\n\n"
        "Точну комплектацію та кошторис визначаємо після короткого опису об'єкта.\n\n"
        f"Напишіть нам: {BOT}\nСайт: {SITE}\n📍 {LOCATION}\n\n{HASHTAGS}"
    )


def make_post(day_index, current, slot_index, slot, product_images):
    time_text, content_format, variant, platforms, aspect = slot
    topic = TOPICS[(day_index * 5 + slot_index * 3) % len(TOPICS)]
    product = PRODUCTS[(day_index * 2 + variant + slot_index) % len(PRODUCTS)]
    service = SERVICES[(day_index + slot_index) % len(SERVICES)]
    presenter = "Сергій" if (day_index + slot_index) % 2 == 0 else "Аліса"
    if content_format == "Товар":
        title, body, price, source = product[0], f"{product[1]}. {product[3]}", product[2], product[4]
        question = f"{product[0]} — підійде для вашого об'єкта?"
        cta = "Запитайте ціну й монтаж →"
        product_category = (
            "recorders" if product[0].startswith("Hikvision iDS")
            else "ajax" if product[0].startswith("Ajax")
            else "intercoms" if product[0].startswith("Dahua DHI-VTH")
            else "cameras"
        )
        category_images = product_images[product_category]
        background = category_images[(day_index + variant) % len(category_images)]
    elif content_format == "Послуга":
        title, body, price, source = service[0], service[1], service[2], SITE
        question = f"Коли востаннє ви перевіряли: {service[0].lower()}?"
        cta = "Замовити консультацію →"
        background = CHARACTERS[(day_index + slot_index) % 2]
    else:
        title, question, brand, body = topic
        price, source = None, SOURCES[(day_index + slot_index) % len(SOURCES)]
        if content_format == "Reels":
            question = f"СТОП: {question}"
            body = f"Перші 3 секунди — проблема. Далі показуємо тест або приклад. Висновок: {body}"
            cta = "Дивіться й напишіть нам →"
        elif content_format == "Обговорення":
            question = question + " Напишіть вашу думку."
            body = f"Позиція ALT-CAM: {body} А як це працює на вашому об'єкті?"
            cta = "Відповідайте в коментарях ↓"
        elif content_format == "Стаття":
            body = f"У статті розбираємо принцип роботи, типові помилки, критерії вибору та практичний чек-лист. {body}"
            cta = "Отримати чек-лист →"
        else:
            body = f"Коротко про головне: {body} Підбір починаємо не з бренду, а з умов об'єкта."
            cta = "Поставте питання →"
        background = CHARACTERS[(day_index + slot_index) % 2] if slot_index % 3 == 0 else product_images["all"][(day_index * 7 + slot_index) % len(product_images["all"])]
    caption = base_caption(title, question, body, price)
    scheduled = f"{current.isoformat()}T{time_text}:00+03:00"
    slug = f"altcam-aug-{current.isoformat()}-{slot_index+1:02d}"
    carousel_titles = [question]
    if content_format == "Reels":
        carousel_titles = [
            question,
            "Чому це стається?",
            "Рішення без зайвого обладнання",
            f"{presenter} показує результат ALT-CAM",
        ]
    elif content_format == "Товар":
        carousel_titles = [question, product[3], f"Ціна: {price}", "Підбір і монтаж від ALT-CAM"]
    elif content_format == "Послуга":
        carousel_titles = [question, body, f"Вартість: {price}", "Роботу виконує ALT-CAM"]
    return {
        "id": slug,
        "day": day_index + 1,
        "slot_index": slot_index,
        "scheduled_at": scheduled,
        "content_format": content_format,
        "variant": variant,
        "presenter": presenter,
        "platforms": platforms,
        "aspect_ratio": aspect,
        "status": "draft",
        "approval_required": True,
        "title": title,
        "question": question,
        "summary": body,
        "price": price,
        "cta_short": cta,
        "carousel_titles": carousel_titles,
        # Research sources stay internal; the public calendar routes only to ALT-CAM.
        "source_url": SITE,
        "caption": caption,
        "captions": {
            "facebook": caption,
            "instagram": caption,
            "threads": f"{question}\n\n{body}\n\nА як у вас?\n{BOT}\n{HASHTAGS}",
            "telegram": f"**{question}**\n\n{body}" + (f"\n\n`{price}`" if price else "") + f"\n\n🤖 Консультація: {BOT}\n📍 {LOCATION}",
            "tiktok": f"{question}\n\n{cta}\n{BOT}\n#AltCam #безпека #Київ #Вишгород",
            "youtube": f"{title} | ALT-CAM Security UA\n\n{body}\n\nКонсультація: {BOT}\nСайт: {SITE}\n📍 {LOCATION}",
        },
    }, background


def selected_platform(post: dict) -> str:
    choices = PUBLISH_DISTRIBUTION[post["content_format"]]
    return choices[(post["day"] + post["slot_index"]) % len(choices)]


def publication_aspect(post: dict, platform: str) -> str:
    if platform == "tiktok" or post["content_format"] == "Reels":
        return "9:16"
    if platform == "instagram" or post["content_format"] in {"Товар", "Послуга", "Пост"}:
        return "4:5"
    return "16:9"


def render_html():
    return '''<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ALT-CAM — серпень 2026</title><style>
:root{color-scheme:dark;--bg:#0b0d12;--panel:#151923;--line:#2b3240;--text:#f7f8fa;--muted:#aab1bf;--gold:#ffcc00;--green:#54dfa0}
*{box-sizing:border-box}body{margin:0;font:15px Inter,system-ui,sans-serif;background:radial-gradient(circle at 10% 0,#332b05 0,transparent 32rem),var(--bg);color:var(--text)}
main{width:min(1280px,calc(100% - 28px));margin:auto;padding:36px 0 60px}header{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}h1{font-size:clamp(32px,5vw,58px);margin:0 0 8px}p{color:var(--muted);line-height:1.55;margin:0}.badge,.chip,button{border:1px solid var(--line);border-radius:999px;padding:9px 12px;background:#ffffff0a;color:var(--text)}.badge{white-space:nowrap}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}button{cursor:pointer}button.active{background:var(--gold);color:#151000;font-weight:800}.grid{display:grid;gap:18px}.day{background:#ffffff08;border:1px solid var(--line);border-radius:22px;overflow:hidden}.day-head{padding:18px 20px;background:#ffffff08;display:flex;justify-content:space-between;border-bottom:1px solid var(--line)}.day-head h2{margin:0}.post{display:grid;grid-template-columns:84px 150px 1fr;gap:16px;padding:18px 20px;border-bottom:1px solid #ffffff0c}.post:last-child{border:0}.time{font-size:17px;color:var(--gold);font-weight:800}.post img{width:150px;max-height:230px;object-fit:cover;border-radius:14px;border:1px solid var(--line)}h3{margin:0 0 7px;font-size:20px}.meta{display:flex;gap:7px;flex-wrap:wrap;margin:11px 0}.chip{font-size:12px;padding:5px 8px}.format{background:var(--gold);color:#181200;font-weight:900}.draft{background:#ff9f43;color:#201000;font-weight:800}details{margin-top:10px;border:1px solid var(--line);border-radius:12px;background:#0003}summary{padding:10px 12px;color:var(--gold);font-weight:700;cursor:pointer}pre{white-space:pre-wrap;font:inherit;padding:0 12px 12px;margin:0}.source{color:#7fd7ff;text-decoration:none}.note{margin-top:20px;padding:15px;border:1px solid #665410;border-radius:16px;background:#ffcc0010;color:#f7e9a7}@media(max-width:760px){header{display:block}.badge{display:inline-block;margin-top:14px}.post{grid-template-columns:1fr}.post img{width:100%;max-height:420px}}
</style></head><body><main><header><div><h1>ALT-CAM • Серпень 2026</h1><p>319 матеріалів: 2 статті, 2 Reels, 2 пости, 2 обговорення, 2 товари та 1 послуга щодня.</p></div><div class="badge">3–31 серпня • 29 днів</div></header>
<nav class="toolbar" id="filters"><button class="active" data-filter="all">Усі</button><button data-filter="Стаття">Статті</button><button data-filter="Reels">Reels</button><button data-filter="Пост">Пости</button><button data-filter="Обговорення">Обговорення</button><button data-filter="Товар">Товари</button><button data-filter="Послуга">Послуги</button></nav><section id="calendar" class="grid"></section><p class="note">Чернетки не публікуються автоматично. Перед статусом READY перевіряємо актуальність ціни, наявність товару, текст і медіа.</p></main>
<script src="./altcam-august-2026-data.js"></script><script>
const data=window.ALT_CAM_AUGUST_2026.posts,cal=document.getElementById('calendar'),filters=document.getElementById('filters');let active='all';
const df=new Intl.DateTimeFormat('uk-UA',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Kyiv'}),tf=new Intl.DateTimeFormat('uk-UA',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Kyiv'});const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function render(){const rows=active==='all'?data:data.filter(p=>p.content_format===active),days=new Map();for(const p of rows){const k=p.scheduled_at.slice(0,10);if(!days.has(k))days.set(k,[]);days.get(k).push(p)}cal.innerHTML=[...days.entries()].map(([k,items])=>`<article class="day"><div class="day-head"><h2>${df.format(new Date(items[0].scheduled_at))}</h2><strong>${items.length} матеріалів</strong></div>${items.map(p=>`<div class="post"><div class="time">${tf.format(new Date(p.scheduled_at))}</div><img src="${p.image_path}" alt="${esc(p.title)}"><div><h3>${esc(p.question)}</h3><p>${esc(p.summary)}</p><div class="meta"><span class="chip format">${p.content_format}</span><span class="chip draft">ЧЕРНЕТКА</span><span class="chip">${p.aspect_ratio}</span><span class="chip">${p.presenter}</span>${p.platforms.map(x=>`<span class="chip">${x}</span>`).join('')}</div><a class="source" href="${p.source_url}" target="_blank" rel="noreferrer">Внутрішнє джерело фактів</a><details><summary>Готові тексти по платформах</summary>${Object.entries(p.captions).map(([n,t])=>`<pre><b>${n}</b>\n${esc(t)}</pre>`).join('')}</details></div></div>`).join('')}</article>`).join('')}
filters.addEventListener('click',e=>{const b=e.target.closest('button[data-filter]');if(!b)return;active=b.dataset.filter;filters.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));render()});render();
</script></body></html>'''


def publisher_post(post: dict) -> dict:
    platform = selected_platform(post)
    captions = dict(post["captions"])
    captions["instagram"] = (
        captions["instagram"].replace(
            f"Напишіть нам: {BOT}\nСайт: {SITE}",
            "Напишіть нам у Direct. Посилання на сайт і Telegram — у шапці профілю.",
        )
    )
    captions["tiktok"] = (
        f"{post['question']}\n\n{post['cta_short']}\n"
        "Посилання на консультацію — у профілі.\n"
        "#AltCam #безпека #Київ #Вишгород"
    )
    if post["content_format"] == "Товар":
        for name, caption in captions.items():
            caption = re.sub(
                r"💰[^\n]*",
                "💰 Актуальна ціна — після перевірки наявності.",
                caption,
            )
            if post.get("price"):
                caption = caption.replace(
                    f"`{post['price']}`",
                    "`Актуальна ціна — після перевірки наявності`",
                )
            captions[name] = caption
    result = {
        "id": post["id"],
        "scheduled_at": post["scheduled_at"],
        "status": "ready",
        "approval_required": False,
        "campaign": "altcam-august-2026",
        "content_format": post["content_format"],
        "presenter": post["presenter"],
        "platforms": [platform],
        "media_type": "image",
        "image_path": post["image_path"],
        "image_url": post["image_url"],
        "image_urls": post.get("image_urls", [post["image_url"]]),
        "tiktok_photo_images": post.get("image_urls", [post["image_url"]]),
        "title": post["title"],
        "caption": captions.get(platform, post["caption"]),
        "captions": captions,
        "funnel": {
            "primary": BOT,
            "secondary": SITE,
            "telegram_channel": "https://t.me/altcam_security_ua",
        },
    }
    if platform == "instagram" and len(result["image_urls"]) > 1:
        result["instagram_media_type"] = "CAROUSEL"
    return result


def main():
    product_images = source_images()
    if not product_images["all"]:
        raise SystemExit("No product images found")
    MEDIA.mkdir(parents=True, exist_ok=True)
    posts = []
    current = date(2026, 8, 3)
    end = date(2026, 8, 31)
    day_index = 0
    while current <= end:
        for slot_index, slot in enumerate(SLOTS):
            post, background = make_post(day_index, current, slot_index, slot, product_images)
            format_slugs = {
                "Стаття": "article",
                "Reels": "reels",
                "Пост": "post",
                "Обговорення": "discussion",
                "Товар": "product",
                "Послуга": "service",
            }
            platform = selected_platform(post)
            post["aspect_ratio"] = publication_aspect(post, platform)
            base_filename = f"{current.isoformat()}-{slot_index+1:02d}-{format_slugs[post['content_format']]}"
            slide_count = 4 if post["content_format"] == "Reels" else 1
            filenames = []
            for slide in range(1, slide_count + 1):
                suffix = f"-slide-{slide:02d}" if slide_count > 1 else ""
                filename = f"{base_filename}{suffix}.jpg"
                output = MEDIA / filename
                slide_background = background
                if slide_count > 1:
                    if slide == slide_count:
                        slide_background = CHARACTERS[0 if post["presenter"] == "Сергій" else 1]
                    elif slide > 1:
                        slide_background = product_images["all"][(day_index * 13 + slot_index * 5 + slide) % len(product_images["all"])]
                render_card(post, slide_background, output, slide=slide, total=slide_count)
                filenames.append(filename)
            filename = filenames[0]
            post["image_path"] = f"../august-2026-media/{filename}"
            post["image_url"] = f"https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/august-2026-media/{filename}"
            post["image_paths"] = [f"../august-2026-media/{name}" for name in filenames]
            post["image_urls"] = [f"https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/august-2026-media/{name}" for name in filenames]
            posts.append(post)
        current += timedelta(days=1)
        day_index += 1
    expected_media = {
        Path(path).name
        for post in posts
        for path in post.get("image_paths", [post["image_path"]])
    }
    for stale in MEDIA.glob("*.jpg"):
        if stale.name not in expected_media:
            stale.unlink()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period": "2026-08-03/2026-08-31",
        "timezone": "Europe/Kyiv",
        "brand": "ALT-CAM Security UA",
        "status": "draft",
        "distribution_note": "11 materials per day distributed across relevant platforms, not 11 duplicates per platform.",
        "posts": posts,
    }
    CALENDAR.mkdir(parents=True, exist_ok=True)
    DATA.write_text("window.ALT_CAM_AUGUST_2026 = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    INDEX.write_text(render_html(), encoding="utf-8")
    (MEDIA / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    queue_payload = {
        "timezone": "Europe/Kyiv",
        "notes": "Approved August 2026 queue. Content is distributed across platforms to avoid cross-platform duplication. YouTube remains manual until API integration.",
        "posts": [publisher_post(post) for post in posts],
    }
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(queue_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(posts)} posts and {len(posts)} media cards")


if __name__ == "__main__":
    main()
