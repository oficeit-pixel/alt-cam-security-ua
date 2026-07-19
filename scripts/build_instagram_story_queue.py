from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "social-posts" / "instagram-catalog"
PUBLIC_BASE = (
    "https://oficeit-pixel.github.io/alt-cam-security-ua/"
    "social-posts/instagram-catalog"
)


def story_item(item_id: str, image_path: str, when: datetime, category: str) -> dict:
    return {
        "id": item_id,
        "scheduled_at": when.isoformat(timespec="seconds"),
        "platforms": ["instagram"],
        "image_path": image_path,
        "image_url": f"{PUBLIC_BASE}/{image_path}",
        "instagram_media_type": "STORIES",
        "highlight_category": category,
        "status": "ready",
        "caption": "",
        "captions": {"instagram": ""},
    }


def main():
    products = json.loads((CATALOG / "products.json").read_text(encoding="utf-8"))
    start = datetime.now().replace(microsecond=0)
    queue: list[dict] = []
    offset = 0
    for category in products["categories"]:
        for index, product in enumerate(category["products"], 1):
            relative = Path(product["card_path"]).relative_to(
                Path("social-posts/instagram-catalog")
            )
            image_path = relative.as_posix()
            queue.append(
                story_item(
                    f"ig-highlight-{category['slug']}-{index:02d}",
                    image_path,
                    start + timedelta(minutes=offset * 2),
                    category["title"],
                )
            )
            offset += 1
    for index in range(1, 11):
        image_path = f"service-cards/{index:02d}-service.jpg"
        queue.append(
            story_item(
                f"ig-highlight-services-{index:02d}",
                image_path,
                start + timedelta(minutes=offset * 2),
                "ПОСЛУГИ",
            )
        )
        offset += 1
    payload = {
        "timezone": "Europe/Kyiv",
        "notes": "Instagram Stories queue for six ALT-CAM highlights.",
        "posts": queue,
    }
    output = CATALOG / "stories.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created {len(queue)} queued stories: {output}")


if __name__ == "__main__":
    main()
