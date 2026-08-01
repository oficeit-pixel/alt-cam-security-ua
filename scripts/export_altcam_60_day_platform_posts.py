from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-03-60-day-matrix"
PLAN_PATH = PLAN_DIR / "plan.json"
OUT = PLAN_DIR / "platform-posts"

PLATFORMS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "telegram": "Telegram",
    "threads": "Threads",
}


def media_link(day: dict, platform: str) -> str:
    media = day.get("media", {})
    if platform == "instagram":
        return media.get("tiktok_cover", "")
    if platform == "facebook":
        return media.get("youtube_thumbnail", "") or media.get("tiktok_cover", "")
    if platform == "telegram":
        return media.get("tiktok_cover", "")
    if platform == "threads":
        return media.get("tiktok_cover", "")
    return ""


def platform_text(day: dict, platform: str) -> str:
    if platform == "facebook":
        return day["instagram_facebook"]["caption"]
    if platform == "instagram":
        return day["instagram_facebook"]["caption"]
    if platform == "telegram":
        return day["telegram"]["text"] + "\n\nКнопка: [ 🤖 Розрахувати вартість у боті ]"
    if platform == "threads":
        return "\n\n".join(day["threads"]["thread_posts"]) + "\n\n" + day["threads"]["first_comment"]
    raise ValueError(platform)


def render_platform_md(plan: dict, platform: str, title: str) -> str:
    lines = [
        f"# ALT-CAM — {title} публікації на 60 днів",
        "",
        f"Період: **{plan['period']['start']} — {plan['period']['end']}**",
        "",
        "Кожен день має унікальний hook, тему, об’єкт, CTA і медіа.",
        "",
        "| День | Дата | Контур | Тема | Медіа |",
        "|---:|---|---|---|---|",
    ]
    for day in plan["days"]:
        link = media_link(day, platform)
        link_md = f"[media]({link})" if link else "—"
        lines.append(f"| {day['day']} | {day['date']} | {day['content_type']} | {day['topic']} | {link_md} |")

    for day in plan["days"]:
        link = media_link(day, platform)
        lines.extend([
            "",
            "---",
            "",
            f"## День {day['day']:02d} — {day['date']} — {day['content_type']}",
            "",
            f"**Тема:** {day['topic']}  ",
            f"**Об’єкт:** {day['object_type']}  ",
            f"**CTA:** {day['keyword']}  ",
            f"**Медіа:** [{Path(link).name}]({link})" if link else "**Медіа:** —",
            "",
            "### Готовий текст",
            "",
            platform_text(day, platform),
            "",
        ])
        if platform == "instagram":
            lines.extend([
                "### Карусель",
                "",
            ])
            for index, slide in enumerate(day["instagram_facebook"]["slides"], 1):
                lines.append(f"{index}. {slide}")
            lines.append("")
        if platform == "threads":
            lines.extend([
                "### Формат публікації",
                "",
                "Публікувати як міні-тред. Кожен пункт `1/7 ... 7/7` — окреме повідомлення.",
                "",
            ])
        if platform == "telegram":
            lines.extend([
                "### Inline-кнопка",
                "",
                "[ 🤖 Розрахувати вартість у боті ](https://t.me/alt_cam_bot)",
                "",
            ])
    return "\n".join(lines)


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    index_lines = [
        "# ALT-CAM — публікації по платформах",
        "",
        "Тут винесені окремі готові тексти для Facebook, Instagram, Telegram і Threads.",
        "",
    ]
    for platform, title in PLATFORMS.items():
        posts = []
        for day in plan["days"]:
            posts.append({
                "day": day["day"],
                "date": day["date"],
                "content_type": day["content_type"],
                "topic": day["topic"],
                "object_type": day["object_type"],
                "keyword": day["keyword"],
                "media": media_link(day, platform),
                "text": platform_text(day, platform),
            })
        md_name = f"{platform}-posts.md"
        json_name = f"{platform}-posts.json"
        (OUT / md_name).write_text(render_platform_md(plan, platform, title), encoding="utf-8")
        (OUT / json_name).write_text(json.dumps({"platform": platform, "posts": posts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index_lines.append(f"- [{title} Markdown]({md_name}) / [{title} JSON]({json_name})")
    (OUT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
