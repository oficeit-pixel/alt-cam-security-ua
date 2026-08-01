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
    variants = ["problem", "product", "alisa", "sergey"]
    return variants[(day["day"] - 1) % len(variants)]


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
    for i in range(0, w, 90):
        draw.line((i, 0, i - 420, h), fill="#17171B", width=3)
    draw.rounded_rectangle((42, 42, w - 42, h - 42), radius=48, fill=PANEL, outline=accent, width=5)
    draw.rectangle((0, h - 345, w, h), fill="#08080A")
    draw.polygon([(0, 174), (w, 64), (w, 142), (0, 252)], fill=accent)
    draw.text((82, 136), loud_badge(day), fill=ANTHRACITE, font=font(42, True))
    draw.rounded_rectangle((74, 84, 330, 154), radius=22, fill="#09090B", outline=accent, width=2)
    draw.text((105, 101), f"ДЕНЬ {day['day']:02d}", fill=accent, font=font(34, True))
    draw.text((360, 99), day["content_type"].upper(), fill=WHITE, font=font(34, True))

    draw_logo(draw, 82, 230, 1)
    draw.text((174, 236), "ALT-CAM", fill=WHITE, font=font(54, True))
    draw.text((178, 292), "Security UA", fill=MUTED, font=font(26, False))

    scene_label, scene_note = draw_scene(draw, day, accent)
    draw.rounded_rectangle((720, 245, 995, 318), radius=24, fill="#09090B", outline=accent, width=2)
    draw.text((748, 264), scene_label, fill=accent, font=font(26, True))

    hook = short_hook(day)
    title_font = font(82, True)
    title_lines = wrap(draw, hook, title_font, 610)
    y = 465
    for line in title_lines[:5]:
        draw.text((82, y + 6), line, fill="#000000", font=title_font)
        draw.text((82, y), line, fill=WHITE, font=title_font)
        y += 94

    draw.rectangle((82, y + 28, 680, y + 44), fill=accent)
    y += 110
    subtitle = f"{scene_note} • {day['object_type']} • {day['category']} • {day['brands']}"
    for line in wrap(draw, subtitle, font(34, False), 900)[:3]:
        draw.text((82, y), line, fill=MUTED, font=font(34, False))
        y += 48

    card_y = 1230
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

    scene_label, _ = draw_scene(draw, day, accent, landscape=True)
    draw.rounded_rectangle((918, 520, 1192, 580), radius=18, fill="#09090B", outline=accent, width=2)
    draw.text((948, 535), scene_label, fill=accent, font=font(24, True))

    hook = short_hook(day)
    title_font = font(58, True)
    y = 230
    for line in wrap(draw, hook, title_font, 680)[:4]:
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
