import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
POSTS_FILE = ROOT / "posts.json"
STATE_FILE = ROOT / "state.json"
ENV_FILE = ROOT / ".env"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def graph_url(path: str) -> str:
    version = os.getenv("META_GRAPH_VERSION", "v21.0").strip().lstrip("/")
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


def post_graph(path: str, token: str, data: dict) -> dict:
    payload = dict(data)
    payload["access_token"] = token
    response = requests.post(graph_url(path), data=payload, timeout=60)
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    if not response.ok:
        raise RuntimeError(f"Graph API error {response.status_code} for {path}: {body}")
    return body


def publish_facebook(post: dict) -> dict:
    page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    if not page_id or not token:
        raise RuntimeError("FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN is missing.")
    return post_graph(
        f"{page_id}/photos",
        token,
        {
            "url": post["image_url"],
            "caption": post["caption"],
            "published": "true",
        },
    )


def publish_instagram(post: dict) -> dict:
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "").strip()
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not ig_user_id or not token:
        raise RuntimeError("INSTAGRAM_USER_ID or INSTAGRAM_ACCESS_TOKEN is missing.")

    container = post_graph(
        f"{ig_user_id}/media",
        token,
        {
            "image_url": post["image_url"],
            "caption": post["caption"],
        },
    )
    creation_id = container.get("id")
    if not creation_id:
        raise RuntimeError(f"Instagram did not return creation container id: {container}")
    published = post_graph(
        f"{ig_user_id}/media_publish",
        token,
        {"creation_id": creation_id},
    )
    return {"container": container, "published": published}


def publish_threads(post: dict) -> dict:
    threads_user_id = os.getenv("THREADS_USER_ID", "").strip()
    token = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    if not threads_user_id or not token:
        raise RuntimeError("THREADS_USER_ID or THREADS_ACCESS_TOKEN is missing.")

    container = post_graph(
        f"{threads_user_id}/threads",
        token,
        {
            "media_type": "IMAGE",
            "image_url": post["image_url"],
            "text": post["caption"],
        },
    )
    creation_id = container.get("id")
    if not creation_id:
        raise RuntimeError(f"Threads did not return creation container id: {container}")
    published = post_graph(
        f"{threads_user_id}/threads_publish",
        token,
        {"creation_id": creation_id},
    )
    return {"container": container, "published": published}


PUBLISHERS = {
    "facebook": publish_facebook,
    "instagram": publish_instagram,
    "threads": publish_threads,
}


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def is_due(post: dict, now: datetime, force: bool) -> bool:
    if force:
        return True
    scheduled = parse_dt(post["scheduled_at"])
    return scheduled <= now


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish due ALT-CAM posts to Meta platforms.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be published without posting.")
    parser.add_argument("--force", action="store_true", help="Publish selected posts even if scheduled time is in the future.")
    parser.add_argument("--post-id", help="Publish only one post id.")
    parser.add_argument("--platform", choices=sorted(PUBLISHERS), action="append", help="Limit to one or more platforms.")
    args = parser.parse_args()

    load_env_file(ENV_FILE)
    dry_run = args.dry_run or os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes", "on"}
    platforms_filter = set(args.platform or [])

    data = load_json(POSTS_FILE, {})
    posts = data.get("posts", [])
    state = load_json(STATE_FILE, {"published": {}})
    state.setdefault("published", {})

    now = datetime.now(timezone.utc).astimezone()
    selected = []
    for post in posts:
        if args.post_id and post["id"] != args.post_id:
            continue
        if not is_due(post, now, args.force):
            continue
        selected.append(post)

    if not selected:
        print("No due posts.")
        return 0

    for post in selected:
        post_state = state["published"].setdefault(post["id"], {})
        platforms = [p for p in post.get("platforms", []) if p in PUBLISHERS]
        if platforms_filter:
            platforms = [p for p in platforms if p in platforms_filter]

        for platform in platforms:
            if post_state.get(platform) and not args.force:
                print(f"SKIP already published: {post['id']} -> {platform}")
                continue

            print(f"{'DRY ' if dry_run else ''}PUBLISH {post['id']} -> {platform}")
            if dry_run:
                continue

            result = PUBLISHERS[platform](post)
            post_state[platform] = {
                "published_at": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
            save_json(STATE_FILE, state)

    if dry_run:
        print("Dry run complete. Set DRY_RUN=false in .env to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
