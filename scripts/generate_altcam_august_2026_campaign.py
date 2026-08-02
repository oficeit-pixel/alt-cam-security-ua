from __future__ import annotations

import json
import math
import textwrap
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / "social-posts" / "calendar"
MEDIA = ROOT / "social-posts" / "august-2026-media"
DATA = CALENDAR / "altcam-august-2026-data.js"
INDEX = CALENDAR / "index.html"
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

COLORS = [(255, 204, 0), (0, 210, 255), (255, 86, 64), (85, 226, 145), (180, 95, 255)]


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


def gradient(size, accent):
    w, h = size
    image = Image.new("RGB", size, (9, 12, 18))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    radius = int(max(w, h) * .52)
    cx, cy = int(w * .82), int(h * .15)
    gd.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=accent + (115,))
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 2))
    return Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")


def render_card(post: dict, background_path: Path, output: Path):
    sizes = {"9:16": (1080, 1920), "4:5": (1080, 1350), "16:9": (1280, 720)}
    size = sizes[post["aspect_ratio"]]
    accent = COLORS[(post["day"] + post["slot_index"]) % len(COLORS)]
    canvas = gradient(size, accent)
    bg = Image.open(background_path).convert("RGB")
    bg = ImageOps.fit(bg, size, method=Image.Resampling.LANCZOS)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)
    bg = ImageEnhance.Color(bg).enhance(1.1)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    if post["aspect_ratio"] == "16:9":
        od.rectangle((0, 0, int(size[0] * .64), size[1]), fill=(5, 8, 14, 218))
        od.rectangle((int(size[0] * .6), 0, size[0], size[1]), fill=(5, 8, 14, 65))
        text_width, x, y = int(size[0] * .53), 64, 92
        title_size, small_size = 58, 27
    else:
        od.rectangle((0, 0, size[0], size[1]), fill=(5, 8, 14, 72))
        od.rectangle((0, 0, size[0], int(size[1] * .48)), fill=(5, 8, 14, 220))
        od.rectangle((0, int(size[1] * .78), size[0], size[1]), fill=(5, 8, 14, 224))
        text_width, x, y = size[0] - 112, 56, 92
        title_size, small_size = (70 if post["aspect_ratio"] == "9:16" else 60), 29
    canvas = Image.blend(canvas, bg, .55)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x, y, x + 230, y + 48), radius=24, fill=accent + (255,))
    draw.text((x + 20, y + 10), post["content_format"].upper(), font=font(22, True), fill=(8, 10, 14))
    y += 78
    title_font = font(title_size, True)
    lines = wrap(draw, post["question"], title_font, text_width)
    for line in lines[:4]:
        draw.text((x, y), line, font=title_font, fill=(255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0))
        y += title_size * 1.08
    draw.line((x, y + 14, x + min(300, text_width), y + 14), fill=accent, width=8)
    if post["aspect_ratio"] == "16:9":
        bottom_y = size[1] - 135
    else:
        bottom_y = size[1] - 185
    draw.text((x, bottom_y), "ALT-CAM SECURITY UA", font=font(small_size, True), fill=accent)
    draw.text((x, bottom_y + 42), post["cta_short"], font=font(small_size, True), fill=(255, 255, 255))
    draw.text((x, bottom_y + 82), "Київ • Вишгород • область", font=font(22), fill=(210, 214, 222))
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
        "source_url": source,
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
            filename = f"{current.isoformat()}-{slot_index+1:02d}-{format_slugs[post['content_format']]}.jpg"
            output = MEDIA / filename
            if not output.exists():
                render_card(post, background, output)
            post["image_path"] = f"../august-2026-media/{filename}"
            post["image_url"] = f"https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/august-2026-media/{filename}"
            posts.append(post)
        current += timedelta(days=1)
        day_index += 1
    expected_media = {Path(post["image_path"]).name for post in posts}
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
    print(f"Generated {len(posts)} posts and {len(posts)} media cards")


if __name__ == "__main__":
    main()
