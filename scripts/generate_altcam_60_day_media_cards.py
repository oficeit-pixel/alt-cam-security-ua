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


def cover_card(day: dict, out: Path) -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), ANTHRACITE)
    draw = ImageDraw.Draw(img)

    accent = contour_color(day["content_type"])
    draw.rounded_rectangle((58, 58, w - 58, h - 58), radius=44, fill=PANEL, outline=LINE, width=2)
    draw.rectangle((0, h - 330, w, h), fill="#09090B")
    draw.rounded_rectangle((74, 84, 330, 154), radius=22, fill=accent)
    draw.text((105, 101), f"ДЕНЬ {day['day']:02d}", fill=ANTHRACITE, font=font(34, True))
    draw.text((360, 99), day["content_type"].upper(), fill=accent, font=font(34, True))

    draw_logo(draw, 82, 230, 1)
    draw.text((174, 236), "ALT-CAM", fill=WHITE, font=font(54, True))
    draw.text((178, 292), "Security UA", fill=MUTED, font=font(26, False))

    hook = day["tiktok_shorts_reels"]["visual_hook_first_3s"]
    title_font = font(74, True)
    title_lines = wrap(draw, hook, title_font, 900)
    y = 510
    for line in title_lines[:5]:
        draw.text((82, y), line, fill=WHITE, font=title_font)
        y += 88

    draw.rectangle((82, y + 28, 620, y + 40), fill=YELLOW)
    y += 110
    subtitle = f"{day['object_type']} • {day['category']} • {day['brands']}"
    for line in wrap(draw, subtitle, font(34, False), 900)[:3]:
        draw.text((82, y), line, fill=MUTED, font=font(34, False))
        y += 48

    card_y = 1230
    draw.rounded_rectangle((82, card_y, w - 82, card_y + 260), radius=28, fill=GRAPHITE, outline=LINE, width=2)
    draw.text((118, card_y + 36), "СЦЕНАРІЙ:", fill=YELLOW, font=font(30, True))
    scenario = day["tiktok_shorts_reels"]["generation_frames_3_5"][0]["visual"]
    for line in wrap(draw, scenario, font(30, False), 820)[:4]:
        draw.text((118, card_y + 88), line, fill=WHITE, font=font(30, False))
        card_y += 38

    draw.rounded_rectangle((82, h - 250, w - 82, h - 142), radius=28, fill=YELLOW)
    draw.text((132, h - 220), f"Напишіть «{day['keyword']}» у бот", fill=ANTHRACITE, font=font(40, True))
    draw.text((132, h - 122), "Київ • Вишгород • Київська область", fill=MUTED, font=font(28, False))

    img.save(out, quality=94)


def youtube_thumb(day: dict, out: Path) -> None:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), ANTHRACITE)
    draw = ImageDraw.Draw(img)
    accent = contour_color(day["content_type"])

    draw.rounded_rectangle((36, 36, w - 36, h - 36), radius=36, fill=PANEL, outline=LINE, width=2)
    draw.rectangle((0, h - 134, w, h), fill="#09090B")
    draw_logo(draw, 72, 74, 1)
    draw.text((164, 80), "ALT-CAM", fill=WHITE, font=font(48, True))
    draw.text((168, 132), day["content_type"].upper(), fill=accent, font=font(25, True))

    draw.rounded_rectangle((980, 70, 1188, 132), radius=18, fill=accent)
    draw.text((1018, 85), f"DAY {day['day']:02d}", fill=ANTHRACITE, font=font(28, True))

    hook = day["tiktok_shorts_reels"]["visual_hook_first_3s"]
    title_font = font(58, True)
    y = 230
    for line in wrap(draw, hook, title_font, 840)[:4]:
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
        "Стиль: реалістичний security-tech ALT-CAM, антрацит/графіт, жовтий #FFCC00, монтажник у брендованій формі.",
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
