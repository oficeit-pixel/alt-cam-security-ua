from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "social-posts" / "instagram-catalog" / "service-cards"
SOURCE = ROOT / "social-posts" / "images" / "calendar-2026"

SERVICES = [
    (
        "Консультація та розрахунок",
        "БЕЗКОШТОВНО",
        ["Уточнення задачі", "Підбір рішення", "Попередній бюджет"],
        "altcam-2026-07-29-04-security-audit-template.jpg",
    ),
    (
        "Виїзд та аудит об'єкта",
        "від 475 грн",
        ["Огляд зон контролю", "Оцінка трас і живлення", "Базова схема системи"],
        "altcam-2026-08-02-04-what-to-do-before-buy.jpg",
    ),
    (
        "Монтаж внутрішньої камери",
        "від 1 045 грн",
        ["Встановлення", "Підключення", "Налаштування огляду"],
        "altcam-2026-07-29-01-hikvision-4mp-review.jpg",
    ),
    (
        "Монтаж вуличної камери",
        "від 1 140 грн",
        ["Встановлення", "Герметизація", "Перевірка нічного режиму"],
        "altcam-2026-07-20-01-camera-price-hook.jpg",
    ),
    (
        "Реєстратор і телефон",
        "від 760 грн",
        ["Налаштування NVR/XVR", "Запис та архів", "Віддалений перегляд"],
        "altcam-2026-08-01-03-via-nvr-small-business.jpg",
    ),
    (
        "Монтаж відеодомофона",
        "від 665 грн",
        ["Монтаж монітора", "Підключення панелі", "Перевірка виклику й замка"],
        "altcam-2026-07-20-02-intercom-dahua.jpg",
    ),
    (
        "Домофон у смартфоні",
        "від 1 045 грн",
        ["Підключення до мережі", "Налаштування застосунку", "Тест віддаленої відповіді"],
        "altcam-2026-07-30-02-intercom-phone-pain.jpg",
    ),
    (
        "Монтаж і запуск Ajax",
        "від 855 грн",
        ["Хаб і базові датчики", "Користувачі та кімнати", "Перевірка тривог"],
        "altcam-2026-07-20-03-ajax-starterkit.jpg",
    ),
    (
        "Резервне живлення",
        "від 333 грн",
        ["Підключення резерву", "Перевірка перемикання", "Тест без мережі"],
        "altcam-2026-07-20-04-ups-ritar.jpg",
    ),
    (
        "Безпека під ключ",
        "після аудиту",
        ["Проєкт і кошторис", "Обладнання та монтаж", "Налаштування й інструктаж"],
        "altcam-2026-07-23-03-autonomous-system.jpg",
    ),
]


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size)


def render(index: int, title: str, price: str, includes: list[str], source_name: str):
    w, h = 1080, 1920
    accent = "#ffd400"
    canvas = Image.new("RGB", (w, h), "#090a0d")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, w, 18), fill=accent)
    draw.rounded_rectangle((54, 58, 1026, 174), 28, outline="white", width=2)
    draw.text((84, 83), "ALT-CAM SECURITY UA", font=font(35, True), fill="white")
    draw.text((1000, 91), "ПОСЛУГИ", font=font(25, True), fill=accent, anchor="ra")

    photo = Image.open(SOURCE / source_name).convert("RGB")
    # Calendar creatives place the visual subject on the right and copy on the left.
    # Crop to the subject so old promotional text does not compete with this card.
    crop_left = int(photo.width * 0.64)
    photo = photo.crop((crop_left, 0, photo.width, photo.height))
    photo = ImageOps.fit(photo, (972, 720), method=Image.Resampling.LANCZOS)
    canvas.paste(photo, (54, 220))
    draw.rounded_rectangle((54, 220, 1026, 940), 30, outline=accent, width=5)

    draw.rounded_rectangle((72, 972, 320, 1042), 24, fill=accent)
    draw.text((96, 990), "ПОСЛУГА", font=font(30, True), fill="#090a0d")
    draw.text((72, 1090), title, font=font(50, True), fill="white")

    draw.rounded_rectangle((72, 1255, 650, 1360), 25, outline=accent, width=4)
    draw.text((102, 1280), price, font=font(46, True), fill=accent)

    draw.text((72, 1435), "ЩО ВХОДИТЬ:", font=font(31, True), fill="white")
    y = 1500
    for item in includes:
        draw.text((72, y), f"• {item}", font=font(31), fill="#e7e7e7")
        y += 58

    draw.line((72, 1735, 1008, 1735), fill=accent, width=3)
    draw.text((72, 1770), "Напишіть «КОНСУЛЬТАЦІЯ» у Direct", font=font(35, True), fill="white")
    draw.text((72, 1830), "Київ • Вишгород • Київська область", font=font(26), fill="#c9c9c9")
    draw.text((1008, 1830), f"{index:02d}/10", font=font(26, True), fill=accent, anchor="ra")
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for index, service in enumerate(SERVICES, 1):
        card = render(index, *service)
        card.save(OUT / f"{index:02d}-service.jpg", quality=94, optimize=True)
    print(f"Created {len(SERVICES)} service cards")


if __name__ == "__main__":
    main()
