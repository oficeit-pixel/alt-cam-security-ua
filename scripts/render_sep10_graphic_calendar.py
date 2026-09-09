from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PLAN_ID = "2026-09-10-10-day-product-presentation"
BASE = ROOT / "social-posts" / "content-plans" / PLAN_ID
POSTS_JSON = BASE / "publishing-posts.json"
OUT = BASE / "media" / "full-graphic-calendar.png"


def font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, max_width: int, fnt) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=fnt)
        if bbox[2] - bbox[0] <= max_width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_wrapped(draw, xy, text, max_width, fnt, fill, max_lines=3, line_gap=5):
    x, y = xy
    for line in wrap(draw, text, max_width, fnt)[:max_lines]:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def thumb(path: Path, size=(260, 325)) -> Image.Image:
    w, h = size
    tile = Image.new("RGB", size, "#151515")
    try:
        im = Image.open(path).convert("RGB")
        ratio = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * ratio), int(im.height * ratio)), Image.Resampling.LANCZOS)
        left = (im.width - w) // 2
        top = (im.height - h) // 2
        tile.paste(im.crop((left, top, left + w, top + h)), (0, 0))
    except Exception:
        pass
    return tile


def main() -> None:
    data = json.loads(POSTS_JSON.read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for post in data["posts"]:
        grouped[post["scheduled_at"][:10]].append(post)

    dates = sorted(grouped)
    width = 1920
    header_h = 170
    row_h = 440
    height = header_h + len(dates) * row_h + 60
    img = Image.new("RGB", (width, height), "#0d0d0f")
    draw = ImageDraw.Draw(img)

    gold = "#ffcc00"
    white = "#f5f5f7"
    muted = "#a6a6ad"
    line = "#303033"
    panel = "#151517"

    # Background glow
    draw.ellipse((-260, -240, 620, 430), fill="#231d05")
    draw.text((48, 42), "ALT-CAM SECURITY UA", font=font(44, True), fill=white)
    draw.text((48, 94), "ПОВНИЙ ГРАФІЧНИЙ КАЛЕНДАР: 10–19 ВЕРЕСНЯ 2026", font=font(34, True), fill=gold)
    draw.text((48, 132), "3 товарні пости щодня + 1 Reels/TikTok/Shorts • Facebook • Instagram • Threads • Telegram • TikTok • YouTube Shorts", font=font(22), fill=muted)

    x0 = 48
    y = header_h
    card_w = 390
    gap = 22
    label_w = 150
    thumb_w, thumb_h = 150, 188

    uk_weekdays = {
        0: "Пн",
        1: "Вт",
        2: "Ср",
        3: "Чт",
        4: "Пт",
        5: "Сб",
        6: "Нд",
    }

    for d in dates:
        posts = sorted(grouped[d], key=lambda p: p["scheduled_at"])
        dt = datetime.fromisoformat(posts[0]["scheduled_at"])
        draw.rounded_rectangle((x0, y, width - 48, y + row_h - 24), radius=24, fill=panel, outline=line, width=2)
        draw.text((x0 + 22, y + 26), uk_weekdays[dt.weekday()], font=font(32, True), fill=gold)
        draw.text((x0 + 22, y + 66), dt.strftime("%d.%m"), font=font(36, True), fill=white)
        draw.text((x0 + 22, y + 112), "4 пости", font=font(22), fill=muted)

        cx = x0 + label_w
        for post in posts[:4]:
            media_rel = post.get("preferred_media_path") or post["media_path"]
            media_path = BASE / media_rel
            draw.rounded_rectangle((cx, y + 24, cx + card_w, y + row_h - 48), radius=22, fill="#101012", outline="#2a2a2d", width=2)
            media = thumb(media_path, (thumb_w, thumb_h))
            img.paste(media, (cx + 18, y + 48))
            t = datetime.fromisoformat(post["scheduled_at"]).strftime("%H:%M")
            draw.text((cx + 18, y + 250), t, font=font(30, True), fill=gold)
            draw_wrapped(draw, (cx + 188, y + 48), post["title"], card_w - 212, font(24, True), white, max_lines=5)
            platforms = ", ".join(post["platforms"][:4])
            if len(post["platforms"]) > 4:
                platforms += "…"
            draw_wrapped(draw, (cx + 188, y + 205), platforms, card_w - 212, font(17), muted, max_lines=3)
            status = "AI final" if post.get("preferred_media_path") else "готова картка"
            draw.rounded_rectangle((cx + 18, y + 300, cx + card_w - 18, y + 354), radius=16, fill=gold)
            draw_wrapped(draw, (cx + 36, y + 314), status, card_w - 72, font(20, True), "#050505", max_lines=1)
            cx += card_w + gap
        y += row_h

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, quality=94)
    print(OUT)


if __name__ == "__main__":
    main()
