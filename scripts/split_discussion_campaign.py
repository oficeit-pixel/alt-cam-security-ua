from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "social-posts" / "meta-automation" / "august-priority-posts.json"
TARGET = ROOT / "social-posts" / "meta-automation" / "discussion-posts.json"
STATE = ROOT / "social-posts" / "meta-automation" / "discussion-state.json"


data = json.loads(SOURCE.read_text(encoding="utf-8"))
campaign = [p for p in data.get("posts", []) if p.get("campaign") == "discussion-every-3-hours"]
data["posts"] = [p for p in data.get("posts", []) if p.get("campaign") != "discussion-every-3-hours"]
SOURCE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
TARGET.write_text(
    json.dumps(
        {
            "notes": "ALT-CAM discussion campaign isolated from the main queue",
            "campaign": "discussion-every-3-hours",
            "posts": campaign,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
if not STATE.exists():
    STATE.write_text('{"published": {}}\n', encoding="utf-8")
print(json.dumps({"campaign_posts": len(campaign), "main_posts": len(data["posts"])}, ensure_ascii=False))
