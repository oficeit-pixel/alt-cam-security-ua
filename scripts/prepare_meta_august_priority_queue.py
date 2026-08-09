from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week"
SOURCE = PLAN_DIR / "publishing-posts.json"
TARGET = ROOT / "social-posts" / "meta-automation" / "august-priority-posts.json"
STATE = ROOT / "social-posts" / "meta-automation" / "august-priority-state.json"

RAW_BASE = (
    "https://raw.githubusercontent.com/oficeit-pixel/alt-cam-security-ua/"
    "codex/altcam-august-calendar/"
    "social-posts/content-plans/2026-08-10-product-week/"
)


def raw_url(media_path: str) -> str:
    return RAW_BASE + media_path.replace("\\", "/")


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_posts = data["posts"]
    product_posts = [
        post
        for post in source_posts
        if post.get("media_type") == "image" and post.get("media_path", "").startswith("media/square/")
    ]
    vertical_posts = [
        post
        for post in source_posts
        if post.get("media_type") == "image" and post.get("media_path", "").startswith("media/vertical/")
    ]

    if len(product_posts) < 27:
        raise RuntimeError(f"Need 27 product posts, found {len(product_posts)}")
    if len(vertical_posts) < 4:
        raise RuntimeError(f"Need 4 vertical story covers, found {len(vertical_posts)}")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    queue: list[dict] = []

    announcement_source = product_posts[0]
    announcement_caption = (
        "Оголошення ALT-CAM Security UA\n\n"
        "Підбираємо, встановлюємо та налаштовуємо системи безпеки під ваш об’єкт: "
        "відеоспостереження, домофонія, СКУД, Ajax, резервне живлення, кабель та монтаж.\n\n"
        "Напишіть «ПІДБІР» — підкажемо рішення без зайвого обладнання.\n"
        "🤖 https://t.me/alt_cam_bot\n"
        "🌐 https://alt-cam.net.ua\n"
        "📍 Київ • Вишгород • Київська область\n\n"
        "#AltCam #відеоспостереження #монтажкамер #домофон #Ajax #Київ #Вишгород"
    )
    queue.append(
        {
            "id": "meta-priority-instagram-announcement-2026-08-09",
            "campaign": "altcam-august-priority-meta",
            "scheduled_at": (now - timedelta(minutes=2)).isoformat(),
            "status": "ready",
            "platforms": ["instagram", "threads", "telegram"],
            "media_type": "image",
            "image_url": raw_url(announcement_source["media_path"]),
            "captions": {
                "instagram": announcement_caption,
                "threads": announcement_caption,
                "telegram": announcement_caption,
            },
            "caption": announcement_caption,
        }
    )

    for index, post in enumerate(product_posts[:27]):
        scheduled_at = now + timedelta(minutes=60 * index)
        platforms = ["instagram", "threads", "telegram"]
        if index < 12:
            platforms.insert(0, "facebook")
        queue.append(
            {
                "id": f"meta-priority-{post['id']}",
                "campaign": "altcam-august-priority-meta",
                "scheduled_at": scheduled_at.isoformat(),
                "status": "ready",
                "platforms": platforms,
                "media_type": "image",
                "image_url": raw_url(post["media_path"]),
                "captions": {
                    "facebook": post.get("captions", {}).get("facebook", post.get("caption", "")),
                    "instagram": post.get("captions", {}).get("instagram", post.get("caption", "")),
                    "threads": post.get("captions", {}).get("threads", post.get("caption", "")),
                    "telegram": post.get("captions", {}).get("telegram", post.get("caption", "")),
                },
                "caption": post.get("caption", ""),
            }
        )

    for index, post in enumerate(vertical_posts[:4]):
        scheduled_at = now + timedelta(minutes=15 + 180 * index)
        caption = post.get("caption", "ALT-CAM Security UA")
        queue.append(
            {
                "id": f"meta-priority-story-{post['id']}",
                "campaign": "altcam-august-priority-meta",
                "scheduled_at": scheduled_at.isoformat(),
                "status": "ready",
                "platforms": ["instagram_story", "facebook_story"],
                "media_type": "image",
                "instagram_media_type": "STORIES",
                "image_url": raw_url(post["media_path"]),
                "captions": {"instagram": caption, "facebook": caption},
                "caption": caption,
            }
        )

    TARGET.write_text(
        json.dumps(
            {
                "notes": (
                    "Priority queue: 1 Instagram announcement, 27 Instagram posts, "
                    "12 Facebook posts, Threads + Telegram duplicates, "
                    "4 Instagram stories, 4 Facebook stories."
                ),
                "generated_at": now.isoformat(),
                "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
                "posts": queue,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if not STATE.exists():
        STATE.write_text(json.dumps({"published": {}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {TARGET}")
    print(f"posts={len(queue)} regular_instagram=28 regular_facebook=12 threads=28 telegram=28 stories=4x2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
