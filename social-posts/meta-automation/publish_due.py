import argparse
import json
import os
import sys
import time
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


def github_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def warn(message: str) -> None:
    print(f"::warning::{github_escape(message)}")


def error(message: str) -> None:
    print(f"::error::{github_escape(message)}")


def graph_url(path: str) -> str:
    version = os.getenv("META_GRAPH_VERSION", "v21.0").strip().lstrip("/")
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


def instagram_url(path: str) -> str:
    version = os.getenv("INSTAGRAM_GRAPH_VERSION", "").strip().strip("/")
    if version:
        return f"https://graph.instagram.com/{version}/{path.lstrip('/')}"
    return f"https://graph.instagram.com/{path.lstrip('/')}"


def threads_url(path: str) -> str:
    version = os.getenv("THREADS_GRAPH_VERSION", "").strip().strip("/")
    if version:
        return f"https://graph.threads.net/{version}/{path.lstrip('/')}"
    return f"https://graph.threads.net/{path.lstrip('/')}"


def tiktok_url(path: str) -> str:
    return f"https://open.tiktokapis.com/{path.lstrip('/')}"


def require_env(*names: str) -> dict[str, str]:
    values = {name: os.getenv(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"Missing environment variable(s): {', '.join(missing)}")
    return values


def post_graph(path: str, token: str, data: dict, *, base: str = "facebook") -> dict:
    payload = dict(data)
    payload["access_token"] = token
    if base == "instagram":
        url = instagram_url(path)
    elif base == "threads":
        url = threads_url(path)
    else:
        url = graph_url(path)
    response = requests.post(url, data=payload, timeout=60)
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    if not response.ok:
        raise RuntimeError(f"Graph API error {response.status_code} for {path}: {body}")
    return body


def get_graph(path: str, token: str, params: dict | None = None, *, base: str = "facebook") -> dict:
    payload = dict(params or {})
    payload["access_token"] = token
    if base == "instagram":
        url = instagram_url(path)
    elif base == "threads":
        url = threads_url(path)
    else:
        url = graph_url(path)
    response = requests.get(url, params=payload, timeout=60)
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    if not response.ok:
        raise RuntimeError(f"Graph API error {response.status_code} for {path}: {body}")
    return body


def post_json(url: str, token: str, payload: dict) -> dict:
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json=payload,
        timeout=60,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    if not response.ok:
        raise RuntimeError(f"HTTP error {response.status_code} for {url}: {body}")
    error_info = body.get("error") or {}
    if error_info.get("code") not in {None, "", "ok"}:
        raise RuntimeError(f"API error for {url}: {body}")
    return body


def publish_facebook(post: dict) -> dict:
    env = require_env("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN")
    return post_graph(
        f"{env['FACEBOOK_PAGE_ID']}/photos",
        env["FACEBOOK_PAGE_ACCESS_TOKEN"],
        {
            "url": post["image_url"],
            "caption": caption_for(post, "facebook"),
            "published": "true",
        },
    )


def publish_instagram(post: dict) -> dict:
    env = require_env("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN")
    ig_user_id = env["INSTAGRAM_USER_ID"]
    token = env["INSTAGRAM_ACCESS_TOKEN"]
    api_base = "instagram" if token.startswith("IG") else "facebook"

    container = post_graph(
        f"{ig_user_id}/media",
        token,
        {
            "image_url": post["image_url"],
            "caption": caption_for(post, "instagram"),
        },
        base=api_base,
    )
    creation_id = container.get("id")
    if not creation_id:
        raise RuntimeError(f"Instagram did not return creation container id: {container}")

    container_status = wait_for_instagram_container(creation_id, token, api_base)
    published = post_graph(
        f"{ig_user_id}/media_publish",
        token,
        {"creation_id": creation_id},
        base=api_base,
    )
    return {"container": container, "status": container_status, "published": published}


def wait_for_instagram_container(creation_id: str, token: str, api_base: str) -> dict:
    last_status = {}
    for attempt in range(1, 16):
        last_status = get_graph(
            creation_id,
            token,
            {"fields": "status_code"},
            base=api_base,
        )
        status_code = last_status.get("status_code")
        if status_code == "FINISHED":
            return last_status
        if status_code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram container is not publishable: {last_status}")
        print(
            "WAIT instagram media container "
            f"{creation_id}: status={status_code or 'unknown'} attempt={attempt}/15"
        )
        time.sleep(4)
    raise RuntimeError(f"Instagram container was not ready after waiting: {last_status}")


def publish_threads(post: dict) -> dict:
    env = require_env("THREADS_USER_ID", "THREADS_ACCESS_TOKEN")
    threads_user_id = env["THREADS_USER_ID"]
    token = env["THREADS_ACCESS_TOKEN"]

    container = post_graph(
        f"{threads_user_id}/threads",
        token,
        {
            "media_type": "IMAGE",
            "image_url": post["image_url"],
            "text": caption_for(post, "threads"),
        },
        base="threads",
    )
    creation_id = container.get("id")
    if not creation_id:
        raise RuntimeError(f"Threads did not return creation container id: {container}")
    published = post_graph(
        f"{threads_user_id}/threads_publish",
        token,
        {"creation_id": creation_id},
        base="threads",
    )
    return {"container": container, "published": published}


def publish_telegram(post: dict) -> dict:
    env = require_env("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
    token = env["TELEGRAM_BOT_TOKEN"]
    chat_id = env["TELEGRAM_CHAT_ID"]
    caption = caption_for(post, "telegram")
    api_base = f"https://api.telegram.org/bot{token}"

    photo_payload = {
        "chat_id": chat_id,
        "photo": post["image_url"],
    }
    followup = None
    if len(caption) <= 1024:
        photo_payload["caption"] = caption
    else:
        photo_payload["caption"] = caption[:1000].rstrip() + "…"
        followup = caption

    photo_response = requests.post(
        f"{api_base}/sendPhoto",
        data=photo_payload,
        timeout=60,
    )
    try:
        photo_body = photo_response.json()
    except Exception:
        photo_body = {"raw": photo_response.text}
    if not photo_response.ok or not photo_body.get("ok"):
        raise RuntimeError(f"Telegram sendPhoto failed: {photo_body}")

    result = {"photo": photo_body}
    if followup:
        message_response = requests.post(
            f"{api_base}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": followup[:4096],
                "disable_web_page_preview": "true",
            },
            timeout=60,
        )
        try:
            message_body = message_response.json()
        except Exception:
            message_body = {"raw": message_response.text}
        if not message_response.ok or not message_body.get("ok"):
            raise RuntimeError(f"Telegram sendMessage failed: {message_body}")
        result["message"] = message_body
    return result


def publish_tiktok(post: dict) -> dict:
    env = require_env("TIKTOK_ACCESS_TOKEN")
    token = env["TIKTOK_ACCESS_TOKEN"]
    post_mode = os.getenv("TIKTOK_POST_MODE", "MEDIA_UPLOAD").strip().upper()
    if post_mode not in {"MEDIA_UPLOAD", "DIRECT_POST"}:
        raise RuntimeError("TIKTOK_POST_MODE must be MEDIA_UPLOAD or DIRECT_POST.")

    post_info = {
        "title": tiktok_title_for(post),
        "description": caption_for(post, "tiktok"),
    }
    if post_mode == "DIRECT_POST":
        post_info.update(
            {
                "privacy_level": os.getenv("TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE").strip()
                or "PUBLIC_TO_EVERYONE",
                "disable_comment": os.getenv("TIKTOK_DISABLE_COMMENT", "false").lower()
                in {"1", "true", "yes", "on"},
                "auto_add_music": os.getenv("TIKTOK_AUTO_ADD_MUSIC", "true").lower()
                in {"1", "true", "yes", "on"},
            }
        )

    payload = {
        "post_info": post_info,
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_cover_index": 1,
            "photo_images": tiktok_photo_images_for(post),
        },
        "post_mode": post_mode,
        "media_type": "PHOTO",
    }
    return post_json(
        tiktok_url("/v2/post/publish/content/init/"),
        token,
        payload,
    )


PUBLISHERS = {
    "facebook": publish_facebook,
    "instagram": publish_instagram,
    "threads": publish_threads,
    "telegram": publish_telegram,
    "tiktok": publish_tiktok,
}


def caption_for(post: dict, platform: str) -> str:
    return post.get("captions", {}).get(platform) or post["caption"]


def tiktok_title_for(post: dict) -> str:
    title = post.get("titles", {}).get("tiktok") or post.get("title") or post["id"]
    return title[:90]


def tiktok_photo_images_for(post: dict) -> list[str]:
    images = post.get("tiktok_photo_images") or post.get("image_urls") or [post["image_url"]]
    if not isinstance(images, list) or not images:
        raise RuntimeError("TikTok photo post needs image_url, image_urls, or tiktok_photo_images.")
    return images[:35]


def platform_has_credentials(platform: str) -> bool:
    required = {
        "facebook": ("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"),
        "instagram": ("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"),
        "threads": ("THREADS_USER_ID", "THREADS_ACCESS_TOKEN"),
        "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
        "tiktok": ("TIKTOK_ACCESS_TOKEN",),
    }.get(platform, ())
    return all(os.getenv(name, "").strip() for name in required)


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

    published_count = 0
    skipped_count = 0
    failed = []

    for post in selected:
        post_state = state["published"].setdefault(post["id"], {})
        platforms = [p for p in post.get("platforms", []) if p in PUBLISHERS]
        if platforms_filter:
            platforms = [p for p in platforms if p in platforms_filter]

        for platform in platforms:
            if not platform_has_credentials(platform):
                warn(f"Skip not configured platform: {post['id']} -> {platform}")
                skipped_count += 1
                continue

            if post_state.get(platform) and not args.force:
                print(f"SKIP already published: {post['id']} -> {platform}")
                skipped_count += 1
                continue

            print(f"{'DRY ' if dry_run else ''}PUBLISH {post['id']} -> {platform}")
            if dry_run:
                continue

            try:
                result = PUBLISHERS[platform](post)
            except Exception as exc:
                message = f"Publish failed: {post['id']} -> {platform}: {exc}"
                failed.append(message)
                warn(message)
                continue

            post_state[platform] = {
                "published_at": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
            save_json(STATE_FILE, state)
            published_count += 1

    if dry_run:
        print("Dry run complete. Set DRY_RUN=false in .env to publish.")
        return 0

    print(
        "Publish summary: "
        f"published={published_count}, skipped={skipped_count}, failed={len(failed)}"
    )

    if failed:
        print("Some platforms failed, but successful platforms were not blocked.")
        fail_on_error = os.getenv("FAIL_ON_PUBLISH_ERROR", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if fail_on_error:
            if published_count == 0:
                error("All publication attempts failed. Check tokens, permissions, and app access.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
