from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    r"C:\Users\Net_w\.codex\generated_images\019f3167-a726-7c91-9715-a1b9ce714731\call_T64CuiRO17VnlanFLjfVaAqx.png"
)
SQUARE_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week" / "media" / "square"
VERTICAL_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week" / "media" / "vertical"


SQUARE_CARDS = [
    ("generated-01-hikvision-colorvu-bullet.jpg", "DS-2CD1047G3H-LIUF", "ColorVu 3.0 • 4МП • Smart Light", "КАМЕРА"),
    ("generated-02-indoor-cube-camera.jpg", "DS-2CD2443G2-I BLACK", "4МП • офіс / квартира", "КАМЕРА"),
    ("generated-03-wizmind-nvr.jpg", "DHI-NVR58128H-XI", "128 каналів • 8 HDD • AI", "РЕЄСТРАТОР"),
    ("generated-04-qr-access-reader.jpg", "U-PROX SE QR SLIM", "QR / RFID • контроль входу", "СКУД"),
    ("generated-05-poe-network-cabinet.jpg", "PoE + МЕРЕЖЕВА ШАФА", "для IP-камер • порядок у кабелях", "МЕРЕЖА"),
    ("generated-06-ups-backup-power.jpg", "UPS / РЕЗЕРВ ЖИВЛЕННЯ", "камери працюють без світла", "РЕЗЕРВ"),
    ("generated-07-ip-call-panel.jpg", "IP ВИКЛИЧНА ПАНЕЛЬ", "вхід / хвіртка / ворота", "ДОМОФОН"),
    ("generated-08-thermal-perimeter-camera.jpg", "ТЕПЛОВІЗІЙНИЙ ПЕРИМЕТР", "склад / виробництво / периметр", "ПЕРИМЕТР"),
    ("generated-09-ajax-security-kit.jpg", "AJAX КОМПЛЕКТ", "датчики • сирена • смартфон", "AJAX"),
    ("generated-10-installer-service.jpg", "МОНТАЖ ПІД КЛЮЧ", "підбір • монтаж • налаштування", "СЕРВІС"),
]


REEL_COVERS = [
    ("altcam-reel-2026-08-10-01.jpg", "НЕ КУПУЙТЕ КАМЕРУ", "доки не знаєте 3 помилки вибору"),
    ("altcam-reel-2026-08-11-02.jpg", "ДОМОФОН ≠ ПРОСТО ДЗВІНОК", "це контроль входу з телефону"),
    ("altcam-reel-2026-08-12-03.jpg", "СЛІПІ ЗОНИ КОШТУЮТЬ ДОРОГО", "покажемо, як їх закрити"),
    ("altcam-reel-2026-08-13-04.jpg", "КАБЕЛІ МАЮТЬ БУТИ В ПОРЯДКУ", "інакше система підведе"),
    ("altcam-reel-2026-08-14-05.jpg", "СВІТЛО ЗНИКЛО — БЕЗПЕКА НІ", "резерв для камер і мережі"),
    ("altcam-reel-2026-08-15-06.jpg", "AJAX ДЛЯ ДОМУ Й БІЗНЕСУ", "захист, який завжди поруч"),
    ("altcam-reel-2026-08-16-07.jpg", "ALT-CAM ПІДБИРАЄ ПІД ОБʼЄКТ", "без зайвого обладнання"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_square_text(card: Image.Image, title: str, subtitle: str, tag: str) -> Image.Image:
    card = card.convert("RGBA")
    overlay = Image.new("RGBA", card.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((44, 44, 1120, 282), radius=28, fill=(0, 0, 0, 165), outline=(255, 204, 0, 125), width=2)
    draw.text((80, 72), title, font=font(58, True), fill=(245, 245, 247, 255))
    draw.text((82, 152), subtitle, font=font(39), fill=(220, 220, 225, 235))
    tag_width = max(250, int(draw.textlength(tag, font=font(34, True))) + 62)
    draw.rounded_rectangle((80, 210, 80 + tag_width, 260), radius=20, fill=(255, 204, 0, 235))
    draw.text((110, 217), tag, font=font(34, True), fill=(18, 18, 18, 255))
    draw.rounded_rectangle((44, 1238, 1364, 1365), radius=34, fill=(0, 0, 0, 170), outline=(255, 204, 0, 95), width=2)
    draw.text((86, 1260), "ALT-CAM Security UA", font=font(45, True), fill=(245, 245, 247, 255))
    draw.text((760, 1268), "Київ • Вишгород • область", font=font(34), fill=(255, 204, 0, 255))
    return Image.alpha_composite(card, overlay).convert("RGB")


def create_square_cards() -> list[Path]:
    SQUARE_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE).convert("RGB")
    width, height = image.size
    outputs: list[Path] = []
    for index, (filename, title, subtitle, tag) in enumerate(SQUARE_CARDS):
        col = index % 5
        row = index // 5
        box = (
            round(col * width / 5),
            round(row * height / 2),
            round((col + 1) * width / 5),
            round((row + 1) * height / 2),
        )
        card = image.crop(box).resize((1408, 1408), Image.Resampling.LANCZOS)
        card = add_square_text(card, title, subtitle, tag)
        out = SQUARE_DIR / filename
        card.save(out, quality=94, optimize=True)
        outputs.append(out)
    return outputs


def create_reel_covers(square_paths: list[Path]) -> list[Path]:
    VERTICAL_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for index, (filename, title, subtitle) in enumerate(REEL_COVERS):
        base = Image.open(square_paths[index % len(square_paths)]).convert("RGB")
        bg = base.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(18))
        bg = Image.blend(bg, Image.new("RGB", bg.size, (12, 12, 14)), 0.48).convert("RGBA")
        product = base.resize((860, 860), Image.Resampling.LANCZOS).convert("RGBA")
        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle((70, 110, 1010, 500), radius=34, fill=(0, 0, 0, 185), outline=(255, 204, 0, 120), width=3)
        draw.text((104, 152), title, font=font(66, True), fill=(245, 245, 247, 255))
        draw.text((108, 270), subtitle, font=font(42), fill=(255, 204, 0, 255))
        draw.text((108, 382), "ALT-CAM Security UA", font=font(40, True), fill=(245, 245, 247, 240))
        bg.alpha_composite(product, (110, 610))
        draw.rounded_rectangle((70, 1600, 1010, 1815), radius=40, fill=(255, 204, 0, 238))
        draw.text((116, 1645), "НАПИШІТЬ У TELEGRAM", font=font(48, True), fill=(18, 18, 18, 255))
        draw.text((116, 1710), "підберемо рішення під ваш обʼєкт", font=font(34), fill=(18, 18, 18, 235))
        final = Image.alpha_composite(bg, overlay).convert("RGB")
        out = VERTICAL_DIR / filename
        final.save(out, quality=94, optimize=True)
        outputs.append(out)
    return outputs


def main() -> int:
    squares = create_square_cards()
    verticals = create_reel_covers(squares)
    for path in [*squares, *verticals]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
