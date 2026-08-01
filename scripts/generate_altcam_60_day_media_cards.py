from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-03-60-day-matrix"
PLAN_PATH = PLAN_DIR / "plan.json"
MEDIA_DIR = PLAN_DIR / "media"

ANTHRACITE = "#121212"
PANEL = "#1B1B1F"
GRAPHITE = "#2C2C31"
YELLOW = "#FFCC00"
WHITE = "#F5F5F7"
MUTED = "#86868B"
LINE = "#3A3A42"
RED = "#FF3B30"
CYAN = "#66D9EF"
GREEN = "#47D18C"
ORANGE = "#FF9F43"


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


KEYWORD_SLUGS = {
    "КАМЕРА": "camera",
    "ТЕХНОЛОГІЯ": "technology",
    "МОНТАЖ": "installation",
    "КОМПЛЕКТ": "kit",
    "РЕЗЕРВ": "backup-power",
    "ДОСТУП": "remote-access",
    "AJAX": "ajax",
    "ДОМОФОН": "intercom",
    "СКУД": "access-control",
    "БІЗНЕС": "business-security",
    "ДВІР": "yard-security",
    "ТРИВОГА": "false-alarm",
    "ПІДЇЗД": "building-entrance",
    "АУДИТ": "security-audit",
    "АРХІВ": "archive-storage",
}


def slug(day: dict) -> str:
    keyword = day.get("keyword", "")
    return KEYWORD_SLUGS.get(keyword, f"topic-{day['day']:02d}")


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


def draw_logo(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int = 1) -> None:
    size = 74 * scale
    draw.rounded_rectangle((x, y, x + size, y + size), radius=18 * scale, fill=YELLOW)
    draw.rounded_rectangle((x + 18 * scale, y + 25 * scale, x + 56 * scale, y + 50 * scale), radius=8 * scale, fill=ANTHRACITE)
    draw.rectangle((x + 24 * scale, y + 18 * scale, x + 38 * scale, y + 28 * scale), fill=ANTHRACITE)
    draw.ellipse((x + 29 * scale, y + 29 * scale, x + 47 * scale, y + 47 * scale), fill=YELLOW)
    draw.ellipse((x + 34 * scale, y + 34 * scale, x + 42 * scale, y + 42 * scale), fill=ANTHRACITE)


def contour_color(contour: str) -> str:
    if "Captivate" in contour:
        return "#FFCC00"
    if "Expert" in contour:
        return "#66D9EF"
    if "Proof" in contour:
        return "#7CFF8A"
    return "#FF9B4A"


def creative_type(day: dict) -> str:
    variants = ["problem", "product", "alisa", "sergey", "object", "installer", "rack", "entrance"]
    return variants[(day["day"] - 1) % len(variants)]


def layout_type(day: dict) -> str:
    layouts = ["split", "poster", "product-hero", "work-scene", "object-story", "before-after"]
    return layouts[(day["day"] - 1) % len(layouts)]


def loud_badge(day: dict) -> str:
    labels = {
        "Captivate": "НЕ РОБИ ЦЮ ПОМИЛКУ",
        "Expert": "РОЗБІР БЕЗ ВОДИ",
        "Proof": "РЕАЛЬНИЙ ОБ’ЄКТ",
        "Offer": "ГОТОВЕ РІШЕННЯ",
    }
    return labels.get(day["content_type"], "ALT-CAM")


def short_hook(day: dict) -> str:
    hook = day["tiktok_shorts_reels"]["visual_hook_first_3s"]
    replacements = {
        "Міф: ": "",
        "Правда: ": "",
        "Помилка: ": "",
    }
    for old, new in replacements.items():
        hook = hook.replace(old, new)
    return hook.strip()


def draw_camera_product(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW) -> None:
    s = scale
    draw.rounded_rectangle((x, y, x + int(430 * s), y + int(255 * s)), radius=int(38 * s), fill="#F5F5F7", outline="#FFFFFF", width=int(4 * s))
    draw.rounded_rectangle((x + int(48 * s), y + int(40 * s), x + int(260 * s), y + int(210 * s)), radius=int(36 * s), fill="#111114")
    draw.ellipse((x + int(92 * s), y + int(62 * s), x + int(226 * s), y + int(196 * s)), fill="#050506", outline=accent, width=int(10 * s))
    draw.ellipse((x + int(124 * s), y + int(94 * s), x + int(194 * s), y + int(164 * s)), fill="#25252B", outline="#666672", width=int(5 * s))
    draw.ellipse((x + int(148 * s), y + int(112 * s), x + int(174 * s), y + int(138 * s)), fill="#FFFFFF")
    draw.rounded_rectangle((x + int(272 * s), y + int(78 * s), x + int(396 * s), y + int(128 * s)), radius=int(16 * s), fill=accent)
    draw.text((x + int(292 * s), y + int(87 * s)), "4MP", fill=ANTHRACITE, font=font(int(26 * s), True))
    draw.text((x + int(276 * s), y + int(145 * s)), "PoE / NVR", fill=ANTHRACITE, font=font(int(24 * s), True))
    draw.line((x + int(30 * s), y + int(252 * s), x - int(95 * s), y + int(385 * s)), fill=accent, width=int(18 * s))


def draw_ajax_product(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW) -> None:
    s = scale
    draw.rounded_rectangle((x, y, x + int(210 * s), y + int(350 * s)), radius=int(34 * s), fill="#F7F7FA", outline="#FFFFFF", width=int(4 * s))
    draw.ellipse((x + int(72 * s), y + int(88 * s), x + int(138 * s), y + int(154 * s)), fill=accent)
    draw.rounded_rectangle((x + int(40 * s), y + int(212 * s), x + int(170 * s), y + int(242 * s)), radius=int(12 * s), fill="#D9D9DF")
    draw.text((x + int(42 * s), y + int(272 * s)), "AJAX", fill=ANTHRACITE, font=font(int(28 * s), True))


def draw_person(draw: ImageDraw.ImageDraw, x: int, y: int, name: str, accent: str, scale: float = 1.0) -> None:
    s = scale
    skin = "#F1C7A8"
    suit = "#202026"
    draw.ellipse((x + int(96 * s), y, x + int(214 * s), y + int(118 * s)), fill=skin)
    draw.rectangle((x + int(118 * s), y + int(96 * s), x + int(192 * s), y + int(154 * s)), fill=skin)
    draw.rounded_rectangle((x + int(42 * s), y + int(142 * s), x + int(272 * s), y + int(460 * s)), radius=int(46 * s), fill=suit, outline=LINE, width=int(3 * s))
    draw.rectangle((x + int(42 * s), y + int(230 * s), x + int(272 * s), y + int(288 * s)), fill=accent)
    draw.rounded_rectangle((x + int(82 * s), y + int(178 * s), x + int(232 * s), y + int(234 * s)), radius=int(18 * s), fill="#111114")
    draw.text((x + int(102 * s), y + int(190 * s)), "ALT-CAM", fill=WHITE, font=font(int(24 * s), True))
    draw.text((x + int(88 * s), y + int(246 * s)), name.upper(), fill=ANTHRACITE, font=font(int(30 * s), True))
    draw.line((x + int(72 * s), y + int(452 * s), x + int(52 * s), y + int(610 * s)), fill=suit, width=int(42 * s))
    draw.line((x + int(240 * s), y + int(452 * s), x + int(268 * s), y + int(610 * s)), fill=suit, width=int(42 * s))
    draw.line((x + int(35 * s), y + int(200 * s), x - int(48 * s), y + int(332 * s)), fill=suit, width=int(38 * s))
    draw.line((x + int(278 * s), y + int(205 * s), x + int(380 * s), y + int(284 * s)), fill=suit, width=int(38 * s))
    draw.ellipse((x + int(130 * s), y + int(46 * s), x + int(146 * s), y + int(62 * s)), fill="#111114")
    draw.ellipse((x + int(174 * s), y + int(46 * s), x + int(190 * s), y + int(62 * s)), fill="#111114")
    draw.arc((x + int(136 * s), y + int(66 * s), x + int(188 * s), y + int(96 * s)), 10, 170, fill="#111114", width=int(4 * s))


def draw_problem_scene(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW) -> None:
    s = scale
    draw.rounded_rectangle((x, y, x + int(470 * s), y + int(315 * s)), radius=int(34 * s), fill="#0A0A0C", outline=RED, width=int(8 * s))
    draw.rectangle((x + int(20 * s), y + int(28 * s), x + int(450 * s), y + int(255 * s)), fill="#17171C")
    for i in range(5):
        yy = y + int((62 + i * 38) * s)
        draw.line((x + int(35 * s), yy, x + int(430 * s), yy + int(18 * s)), fill="#2E2E35", width=int(7 * s))
    draw.ellipse((x + int(165 * s), y + int(84 * s), x + int(302 * s), y + int(221 * s)), outline=RED, width=int(12 * s))
    draw.line((x + int(155 * s), y + int(236 * s), x + int(315 * s), y + int(58 * s)), fill=RED, width=int(12 * s))
    draw.rounded_rectangle((x + int(72 * s), y + int(260 * s), x + int(402 * s), y + int(352 * s)), radius=int(22 * s), fill=YELLOW)
    draw.text((x + int(95 * s), y + int(282 * s)), "ДОКАЗІВ НЕМАЄ", fill=ANTHRACITE, font=font(int(32 * s), True))


def draw_object_backdrop(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW, kind: str = "house") -> None:
    s = scale
    draw.rounded_rectangle((x, y, x + int(520 * s), y + int(420 * s)), radius=int(38 * s), fill="#101014", outline=accent, width=int(5 * s))
    if kind == "entrance":
        draw.rectangle((x + int(50 * s), y + int(52 * s), x + int(470 * s), y + int(365 * s)), fill="#2C2C31")
        draw.rectangle((x + int(110 * s), y + int(135 * s), x + int(245 * s), y + int(365 * s)), fill="#101014")
        draw.rectangle((x + int(275 * s), y + int(135 * s), x + int(410 * s), y + int(365 * s)), fill="#101014")
        draw.rectangle((x + int(132 * s), y + int(65 * s), x + int(388 * s), y + int(108 * s)), fill=accent)
        draw.text((x + int(156 * s), y + int(72 * s)), "ПІД’ЇЗД", fill=ANTHRACITE, font=font(int(28 * s), True))
    elif kind == "business":
        draw.rectangle((x + int(56 * s), y + int(70 * s), x + int(464 * s), y + int(365 * s)), fill="#24242A")
        for col in range(4):
            for row in range(3):
                xx = x + int((86 + col * 88) * s)
                yy = y + int((105 + row * 62) * s)
                draw.rectangle((xx, yy, xx + int(54 * s), yy + int(36 * s)), fill="#0D0D10", outline="#4A4A55", width=int(2 * s))
        draw.rectangle((x + int(235 * s), y + int(270 * s), x + int(292 * s), y + int(365 * s)), fill="#101014")
    elif kind == "parking":
        draw.rectangle((x + int(40 * s), y + int(70 * s), x + int(480 * s), y + int(330 * s)), fill="#19191F")
        for i in range(4):
            draw.line((x + int((70 + i * 110) * s), y + int(330 * s), x + int((120 + i * 110) * s), y + int(210 * s)), fill="#555560", width=int(5 * s))
        draw.rounded_rectangle((x + int(150 * s), y + int(250 * s), x + int(360 * s), y + int(315 * s)), radius=int(20 * s), fill="#3A3A42")
        draw.ellipse((x + int(180 * s), y + int(300 * s), x + int(220 * s), y + int(340 * s)), fill="#09090B")
        draw.ellipse((x + int(295 * s), y + int(300 * s), x + int(335 * s), y + int(340 * s)), fill="#09090B")
    else:
        draw.polygon([(x + int(65 * s), y + int(210 * s)), (x + int(260 * s), y + int(65 * s)), (x + int(455 * s), y + int(210 * s))], fill="#34343B")
        draw.rectangle((x + int(92 * s), y + int(210 * s), x + int(428 * s), y + int(365 * s)), fill="#24242A")
        draw.rectangle((x + int(230 * s), y + int(260 * s), x + int(290 * s), y + int(365 * s)), fill="#101014")
        draw.rectangle((x + int(130 * s), y + int(245 * s), x + int(190 * s), y + int(295 * s)), fill="#0D0D10", outline=accent, width=int(3 * s))
        draw.rectangle((x + int(330 * s), y + int(245 * s), x + int(390 * s), y + int(295 * s)), fill="#0D0D10", outline=accent, width=int(3 * s))
    draw_camera_product(draw, x + int(360 * s), y + int(45 * s), scale * 0.34, accent)


def draw_ladder(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW) -> None:
    s = scale
    draw.line((x, y, x + int(90 * s), y + int(430 * s)), fill="#C8C8D0", width=int(10 * s))
    draw.line((x + int(105 * s), y, x + int(15 * s), y + int(430 * s)), fill="#C8C8D0", width=int(10 * s))
    for i in range(6):
        yy = y + int((48 + i * 62) * s)
        draw.line((x + int(10 * s), yy, x + int(95 * s), yy), fill=accent, width=int(8 * s))


def draw_installer_work(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW, name: str = "Сергій") -> None:
    s = scale
    draw_object_backdrop(draw, x, y, scale, accent, kind="house")
    draw_ladder(draw, x + int(70 * s), y + int(210 * s), scale * 0.62, accent)
    draw_person(draw, x + int(130 * s), y + int(210 * s), name, accent, scale * 0.55)
    draw.line((x + int(330 * s), y + int(150 * s), x + int(480 * s), y + int(90 * s)), fill=accent, width=int(8 * s))
    draw.ellipse((x + int(465 * s), y + int(74 * s), x + int(505 * s), y + int(114 * s)), fill=RED)


def draw_rack_scene(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW) -> None:
    s = scale
    draw.rounded_rectangle((x, y, x + int(520 * s), y + int(420 * s)), radius=int(38 * s), fill="#0E0E12", outline=accent, width=int(5 * s))
    draw.rounded_rectangle((x + int(70 * s), y + int(50 * s), x + int(250 * s), y + int(370 * s)), radius=int(20 * s), fill="#2A2A31", outline="#555560", width=int(4 * s))
    for i in range(7):
        yy = y + int((78 + i * 38) * s)
        draw.rectangle((x + int(92 * s), yy, x + int(228 * s), yy + int(20 * s)), fill="#111114", outline=accent if i % 3 == 0 else "#4A4A55", width=int(2 * s))
    for i, color in enumerate([YELLOW, GREEN, CYAN, ORANGE, RED]):
        draw.arc((x + int((260 + i * 16) * s), y + int(100 * s), x + int((430 + i * 16) * s), y + int(345 * s)), 205, 332, fill=color, width=int(7 * s))
    draw.text((x + int(300 * s), y + int(60 * s)), "PoE", fill=accent, font=font(int(36 * s), True))
    draw.text((x + int(300 * s), y + int(110 * s)), "NVR", fill=WHITE, font=font(int(36 * s), True))
    draw.text((x + int(300 * s), y + int(160 * s)), "UPS", fill=WHITE, font=font(int(36 * s), True))


def draw_product_kit(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, accent: str = YELLOW) -> None:
    s = scale
    draw.rounded_rectangle((x, y, x + int(560 * s), y + int(430 * s)), radius=int(42 * s), fill="#F1F1F4", outline=accent, width=int(7 * s))
    draw_camera_product(draw, x + int(55 * s), y + int(58 * s), scale * 0.72, accent)
    draw_ajax_product(draw, x + int(365 * s), y + int(58 * s), scale * 0.78, accent)
    draw.rounded_rectangle((x + int(78 * s), y + int(310 * s), x + int(490 * s), y + int(385 * s)), radius=int(20 * s), fill=ANTHRACITE)
    draw.text((x + int(112 * s), y + int(329 * s)), "КАМЕРИ • AJAX • UPS", fill=accent, font=font(int(32 * s), True))


def draw_scene_panel(draw: ImageDraw.ImageDraw, day: dict, x: int, y: int, w: int, h: int, accent: str, variant: str | None = None) -> tuple[str, str]:
    variant = variant or creative_type(day)
    scale = min(w / 620, h / 520)
    px = x + int((w - 560 * scale) / 2)
    py = y + int((h - 430 * scale) / 2)
    if variant == "installer":
        draw_installer_work(draw, px, py, scale, accent, "Сергій")
        return "МОНТАЖНИК У РОБОТІ", "живий монтаж / кабелі / камера"
    if variant == "alisa":
        draw_installer_work(draw, px, py, scale, accent, "Аліса")
        return "АЛІСА НА ОБ’ЄКТІ", "людина + реальна ситуація"
    if variant == "sergey":
        draw_installer_work(draw, px, py, scale, accent, "Сергій")
        return "СЕРГІЙ НА МОНТАЖІ", "монтажник + рішення"
    if variant == "rack":
        draw_rack_scene(draw, px, py, scale, accent)
        return "СЕРВЕРНИЙ ЩИТ", "кабель / PoE / резерв"
    if variant == "entrance":
        draw_object_backdrop(draw, px, py, scale, accent, "entrance")
        return "ОБ’ЄКТ У КАДРІ", "під’їзд / домофон / СКУД"
    if variant == "object":
        kind = ["house", "parking", "business", "entrance"][(day["day"] // 5) % 4]
        draw_object_backdrop(draw, px, py, scale, accent, kind)
        return "ОБ’ЄКТ У КАДРІ", "будинок / офіс / двір"
    if variant == "product":
        draw_product_kit(draw, px, py, scale, accent)
        return "ТОВАР У КАДРІ", "комплект / товар / ціна"
    draw_problem_scene(draw, px, py, scale, accent)
    return "ПРОБЛЕМА В КАДРІ", "факап / біль / рішення"


def draw_scene(draw: ImageDraw.ImageDraw, day: dict, accent: str, landscape: bool = False) -> tuple[str, str]:
    variant = creative_type(day)
    if landscape:
        box = (760, 160)
        scale = 0.82
    else:
        box = (560, 820)
        scale = 1.0

    if variant == "product":
        draw_camera_product(draw, box[0], box[1], scale, accent)
        draw_ajax_product(draw, box[0] + int(250 * scale), box[1] + int(280 * scale), scale * 0.72, accent)
        return "ТОВАР У КАДРІ", "камера / Ajax / PoE"
    if variant == "alisa":
        draw_person(draw, box[0], box[1], "Аліса", accent, scale)
        draw_camera_product(draw, box[0] - int(340 * scale), box[1] + int(330 * scale), scale * 0.68, accent)
        return "АЛІСА ПОКАЗУЄ", "людина + проблема"
    if variant == "sergey":
        draw_person(draw, box[0], box[1], "Сергій", accent, scale)
        draw_ajax_product(draw, box[0] - int(210 * scale), box[1] + int(300 * scale), scale * 0.76, accent)
        return "СЕРГІЙ ВИРІШУЄ", "монтажник + рішення"
    draw_problem_scene(draw, box[0], box[1], scale, accent)
    draw_camera_product(draw, box[0] - int(340 * scale), box[1] + int(390 * scale), scale * 0.58, accent)
    return "ПРОБЛЕМА В КАДРІ", "факап / біль / рішення"


def cover_card(day: dict, out: Path) -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), ANTHRACITE)
    draw = ImageDraw.Draw(img)

    accent = contour_color(day["content_type"])
    layout = layout_type(day)
    for i in range(0, w, 90):
        draw.line((i, 0, i - 420, h), fill="#17171B", width=3)
    draw.rounded_rectangle((42, 42, w - 42, h - 42), radius=48, fill=PANEL, outline=accent, width=5)
    draw.rectangle((0, h - 330, w, h), fill="#08080A")

    if layout in {"poster", "object-story"}:
        draw.polygon([(0, 96), (w, 42), (w, 126), (0, 210)], fill=accent)
        ribbon_y = 92
    elif layout == "before-after":
        draw.polygon([(0, 212), (w, 116), (w, 198), (0, 306)], fill=accent)
        ribbon_y = 174
    else:
        draw.polygon([(0, 174), (w, 64), (w, 142), (0, 252)], fill=accent)
        ribbon_y = 136
    draw.text((82, ribbon_y), loud_badge(day), fill=ANTHRACITE, font=font(42, True))

    draw.rounded_rectangle((74, 84, 330, 154), radius=22, fill="#09090B", outline=accent, width=2)
    draw.text((105, 101), f"ДЕНЬ {day['day']:02d}", fill=accent, font=font(34, True))
    draw.text((360, 99), day["content_type"].upper(), fill=WHITE, font=font(34, True))

    logo_y = 235 if layout not in {"poster", "object-story"} else 250
    draw_logo(draw, 82, logo_y, 1)
    draw.text((174, logo_y + 6), "ALT-CAM", fill=WHITE, font=font(54, True))
    draw.text((178, logo_y + 62), "Security UA", fill=MUTED, font=font(26, False))

    scene_boxes = {
        "split": (560, 420, 450, 500),
        "poster": (95, 430, 890, 520),
        "product-hero": (250, 390, 640, 560),
        "work-scene": (560, 470, 455, 590),
        "object-story": (90, 410, 900, 520),
        "before-after": (520, 445, 480, 520),
    }
    scene_label, scene_note = draw_scene_panel(draw, day, *scene_boxes[layout], accent)
    label_x = 720 if layout in {"split", "work-scene", "before-after"} else 96
    label_y = 245 if layout in {"split", "work-scene", "before-after"} else 965
    draw.rounded_rectangle((label_x, label_y, label_x + 275, label_y + 73), radius=24, fill="#09090B", outline=accent, width=2)
    draw.text((label_x + 28, label_y + 19), scene_label[:18], fill=accent, font=font(24, True))

    hook = short_hook(day)
    title_size = 82
    if layout in {"poster", "product-hero", "object-story"}:
        title_size = 70
    if layout == "work-scene":
        title_size = 74
    title_font = font(title_size, True)
    title_width = 610 if layout == "split" else 870
    if layout in {"work-scene", "before-after"}:
        title_width = 520
    title_x = 82 if layout != "product-hero" else 92
    y = 465 if layout in {"split", "work-scene", "before-after"} else 1035
    if layout == "product-hero":
        y = 1040
    title_lines = wrap(draw, hook, title_font, title_width)
    for line in title_lines[:5]:
        draw.text((title_x, y + 6), line, fill="#000000", font=title_font)
        draw.text((title_x, y), line, fill=WHITE, font=title_font)
        y += title_size + 12

    line_width = 720 if layout not in {"work-scene", "before-after"} else 500
    draw.rectangle((title_x, y + 24, min(title_x + line_width, w - 92), y + 40), fill=accent)
    y += 110
    subtitle = f"{scene_note} • {day['object_type']} • {day['category']} • {day['brands']}"
    subtitle_width = 900 if layout not in {"work-scene", "before-after"} else 500
    for line in wrap(draw, subtitle, font(34, False), subtitle_width)[:3]:
        draw.text((title_x, y), line, fill=MUTED, font=font(34, False))
        y += 48

    card_y = min(max(y + 28, 1220), 1360)
    draw.rounded_rectangle((82, card_y, w - 82, card_y + 260), radius=28, fill=GRAPHITE, outline=accent, width=3)
    draw.text((118, card_y + 36), "ПРОБЛЕМА → РІШЕННЯ:", fill=accent, font=font(30, True))
    scenario = day["tiktok_shorts_reels"]["generation_frames_3_5"][0]["visual"]
    for line in wrap(draw, scenario, font(30, False), 820)[:4]:
        draw.text((118, card_y + 88), line, fill=WHITE, font=font(30, False))
        card_y += 38

    draw.rounded_rectangle((82, h - 250, w - 82, h - 142), radius=28, fill=accent)
    draw.text((132, h - 220), f"Напишіть «{day['keyword']}» у бот", fill=ANTHRACITE, font=font(40, True))
    draw.text((132, h - 122), "Київ • Вишгород • Київська область", fill=MUTED, font=font(28, False))

    img.save(out, quality=94)


def youtube_thumb(day: dict, out: Path) -> None:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), ANTHRACITE)
    draw = ImageDraw.Draw(img)
    accent = contour_color(day["content_type"])
    layout = layout_type(day)

    for i in range(-300, w, 120):
        draw.line((i, 0, i + 520, h), fill="#17171B", width=4)
    draw.rounded_rectangle((36, 36, w - 36, h - 36), radius=36, fill=PANEL, outline=accent, width=4)
    draw.rectangle((0, h - 134, w, h), fill="#09090B")
    draw.polygon([(0, 164), (720, 64), (700, 124), (0, 224)], fill=accent)
    draw.text((62, 118), loud_badge(day), fill=ANTHRACITE, font=font(34, True))
    draw_logo(draw, 72, 74, 1)
    draw.text((164, 80), "ALT-CAM", fill=WHITE, font=font(48, True))
    draw.text((168, 132), day["content_type"].upper(), fill=accent, font=font(25, True))

    draw.rounded_rectangle((980, 70, 1188, 132), radius=18, fill=accent)
    draw.text((1018, 85), f"DAY {day['day']:02d}", fill=ANTHRACITE, font=font(28, True))

    if layout in {"poster", "object-story", "product-hero"}:
        scene_box = (720, 180, 470, 300)
        title_width = 650
    else:
        scene_box = (780, 165, 400, 330)
        title_width = 670
    scene_label, _ = draw_scene_panel(draw, day, *scene_box, accent)
    draw.rounded_rectangle((918, 520, 1192, 580), radius=18, fill="#09090B", outline=accent, width=2)
    draw.text((948, 535), scene_label[:16], fill=accent, font=font(22, True))

    hook = short_hook(day)
    title_font = font(58, True)
    y = 230
    for line in wrap(draw, hook, title_font, title_width)[:4]:
        draw.text((74, y + 5), line, fill="#000000", font=title_font)
        draw.text((74, y), line, fill=WHITE, font=title_font)
        y += 68

    draw.rectangle((76, y + 22, 560, y + 34), fill=YELLOW)
    draw.text((74, h - 102), f"{day['object_type']} • {day['category']} • {day['keyword']}", fill=WHITE, font=font(30, True))
    draw.text((830, h - 102), "Telegram quiz → @alt_cam_bot", fill=YELLOW, font=font(28, True))

    img.save(out, quality=94)


def media_prompt(day: dict) -> str:
    frames = day["tiktok_shorts_reels"]["generation_frames_3_5"]
    lines = [
        f"# День {day['day']:02d} — media prompt",
        "",
        f"Тема: {day['topic']}",
        f"Контур: {day['content_type']}",
        f"Об’єкт: {day['object_type']}",
        "",
        "Стиль: живий кричащий security-tech ALT-CAM, антрацит/графіт, жовтий #FFCC00, крупний продукт або людина в кадрі, монтажник у брендованій формі.",
        f"Варіант заставки: {creative_type(day)} — товар / Аліса / Сергій / проблема чергуються, щоб медіа не повторювалися.",
        "",
        "Кадри для генерації/анімації:",
    ]
    for frame in frames:
        lines.append(f"- {frame['time']} — {frame['purpose']}: {frame['visual']} Текст: “{frame['onscreen_text']}”.")
    lines.extend([
        "",
        "Уникати: кров, зброя, поліція/військовий стиль, випадкові бренди, дрібний нечитабельний текст.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    tiktok_dir = MEDIA_DIR / "tiktok-covers"
    youtube_dir = MEDIA_DIR / "youtube-thumbnails"
    prompts_dir = MEDIA_DIR / "generation-prompts"
    for folder in (tiktok_dir, youtube_dir, prompts_dir):
        folder.mkdir(parents=True, exist_ok=True)

    index = []
    for day in plan["days"]:
        base = f"day-{day['day']:02d}-{slug(day)}"
        tiktok_path = tiktok_dir / f"{base}-tiktok-cover.png"
        youtube_path = youtube_dir / f"{base}-youtube-thumb.png"
        prompt_path = prompts_dir / f"{base}-media-prompt.md"
        cover_card(day, tiktok_path)
        youtube_thumb(day, youtube_path)
        prompt_path.write_text(media_prompt(day), encoding="utf-8")
        day["media"] = {
            "tiktok_cover": str(tiktok_path.relative_to(PLAN_DIR)).replace("\\", "/"),
            "youtube_thumbnail": str(youtube_path.relative_to(PLAN_DIR)).replace("\\", "/"),
            "generation_prompt": str(prompt_path.relative_to(PLAN_DIR)).replace("\\", "/"),
        }
        index.append(day)

    PLAN_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# ALT-CAM — медіа для 60-денного плану",
        "",
        "У папці є готові брендовані заставки:",
        "",
        "- `tiktok-covers/` — вертикальні 9:16 обкладинки для TikTok/Reels/Shorts.",
        "- `youtube-thumbnails/` — горизонтальні thumbnails для YouTube.",
        "- `generation-prompts/` — промпти на 3–5 кадрів для генерації/анімації.",
        "",
        "| День | Тема | TikTok cover | YouTube thumbnail | Prompt |",
        "|---:|---|---|---|---|",
    ]
    for day in index:
        media = day["media"]
        tiktok_link = str(Path(media["tiktok_cover"]).relative_to("media")).replace("\\", "/")
        youtube_link = str(Path(media["youtube_thumbnail"]).relative_to("media")).replace("\\", "/")
        prompt_link = str(Path(media["generation_prompt"]).relative_to("media")).replace("\\", "/")
        lines.append(
            f"| {day['day']} | {day['topic']} | [{Path(media['tiktok_cover']).name}]({tiktok_link}) | "
            f"[{Path(media['youtube_thumbnail']).name}]({youtube_link}) | "
            f"[prompt]({prompt_link}) |"
        )
    (MEDIA_DIR / "MEDIA_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(MEDIA_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
