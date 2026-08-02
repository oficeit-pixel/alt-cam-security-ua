from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "social-posts" / "meta-automation" / "posts.json"
TARGET = ROOT / "social-posts" / "weekly-automation"

POST_MEDIA = {
    "altcam-matrix-2026-08-03-d1": "06-camera-mistakes.png",
    "altcam-matrix-2026-08-04-d2": "01-cameras-before-theft.png",
    "altcam-matrix-2026-08-05-d3": "03-intercom.png",
    "altcam-matrix-2026-08-06-d4": "08-turnkey-installation.png",
    "altcam-matrix-2026-08-07-d5": "05-ups-backup.png",
    "altcam-matrix-2026-08-08-d6": "02-home-video-security.png",
    "altcam-matrix-2026-08-09-d7": "04-ajax.png",
}

IMAGE_BASE = "https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/images"


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    indexed = {post["id"]: post for post in source.get("posts", [])}
    queue = []

    for post_id, filename in POST_MEDIA.items():
        if post_id not in indexed:
            raise SystemExit(f"Missing approved post: {post_id}")
        original = indexed[post_id]
        post = {
            "id": post_id,
            "scheduled_at": original["scheduled_at"],
            "status": "ready",
            "approval_required": False,
            "campaign": "altcam-weekly-matrix-2026-08-03",
            "content_contour": original.get("content_contour"),
            "presenter": original.get("presenter"),
            "platforms": ["facebook", "instagram", "telegram", "tiktok"],
            "media_type": "image",
            "image_path": f"../images/{filename}",
            "image_url": f"{IMAGE_BASE}/{filename}",
            "tiktok_photo_images": [f"{IMAGE_BASE}/{filename}"],
            "caption": original["caption"],
            "captions": {
                key: value
                for key, value in original.get("captions", {}).items()
                if key in {"facebook", "instagram", "telegram", "tiktok"}
            },
            "production_plan": original.get("production_plan"),
        }
        queue.append(post)

    TARGET.mkdir(parents=True, exist_ok=True)
    payload = {
        "timezone": "Europe/Kyiv",
        "notes": "Approved isolated weekly queue. One item per day. YouTube requires a separate API integration.",
        "posts": queue,
    }
    (TARGET / "posts.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    state = TARGET / "state.json"
    if not state.exists():
        state.write_text(json.dumps({"published": {}}, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(queue)} approved posts in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
