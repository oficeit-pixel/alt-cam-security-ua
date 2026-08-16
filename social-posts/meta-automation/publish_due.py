import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
POSTS_FILE = Path(os.getenv("SOCIAL_POSTS_FILE", str(ROOT / "posts.json")))
STATE_FILE = Path(os.getenv("SOCIAL_STATE_FILE", str(ROOT / "state.json")))
ENV_FILE = ROOT / ".env"
TELEGRAM_GROUP_URL = os.getenv(
    "ALT_CAM_TELEGRAM_GROUP_URL",
    "https://t.me/altcam_security_ua",
).strip()


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
    if post.get("media_type") == "video":
        return post_graph(
            f"{env['FACEBOOK_PAGE_ID']}/videos",
            env["FACEBOOK_PAGE_ACCESS_TOKEN"],
            {
                "file_url": post["video_url"],
                "description": caption_for(post, "facebook"),
                "published": "true",
            },
        )
    return post_graph(
        f"{env['FACEBOOK_PAGE_ID']}/photos",
        env["FACEBOOK_PAGE_ACCESS_TOKEN"],
        {
            "url": post["image_url"],
            "caption": caption_for(post, "facebook"),
            "published": "true",
        },
    )


def publish_facebook_story(post: dict) -> dict:
    env = require_env("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = env["FACEBOOK_PAGE_ID"]
    token = env["FACEBOOK_PAGE_ACCESS_TOKEN"]

    if post.get("media_type") == "video":
        raise RuntimeError("Facebook story video publishing is not enabled in this queue; use image stories.")

    photo = post_graph(
        f"{page_id}/photos",
        token,
        {
            "url": post["image_url"],
            "published": "false",
        },
    )
    photo_id = photo.get("id")
    if not photo_id:
        raise RuntimeError(f"Facebook did not return unpublished story photo id: {photo}")

    story = post_graph(
        f"{page_id}/photo_stories",
        token,
        {"photo_id": photo_id},
    )
    return {"photo": photo, "story": story}


def publish_instagram(post: dict) -> dict:
    env = require_env("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN")
    ig_user_id = env["INSTAGRAM_USER_ID"]
    token = env["INSTAGRAM_ACCESS_TOKEN"]
    api_base = "instagram" if token.startswith("IG") else "facebook"

    instagram_media_type = str(post.get("instagram_media_type", "")).upper()
    if instagram_media_type == "CAROUSEL":
        image_urls = post.get("image_urls") or []
        if len(image_urls) < 2:
            raise RuntimeError("Instagram carousel needs at least two image_urls.")
        child_ids = []
        for image_url in image_urls[:10]:
            child = post_graph(
                f"{ig_user_id}/media",
                token,
                {"image_url": image_url, "is_carousel_item": "true"},
                base=api_base,
            )
            child_id = child.get("id")
            if not child_id:
                raise RuntimeError(f"Instagram did not return carousel child id: {child}")
            wait_for_instagram_container(child_id, token, api_base)
            child_ids.append(child_id)
        media_payload = {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption_for(post, "instagram"),
        }
    elif instagram_media_type == "STORIES":
        media_payload = {"media_type": "STORIES"}
        if post.get("media_type") == "video":
            media_payload["video_url"] = post["video_url"]
        else:
            media_payload["image_url"] = post["image_url"]
    elif post.get("media_type") == "video":
        media_payload = {
            "caption": caption_for(post, "instagram"),
        }
        media_payload.update(
            {
                "media_type": "REELS",
                "video_url": post["video_url"],
                "share_to_feed": "true",
            }
        )
    else:
        media_payload = {
            "caption": caption_for(post, "instagram"),
            "image_url": post["image_url"],
        }

    container = post_graph(
        f"{ig_user_id}/media",
        token,
        media_payload,
        base=api_base,
    )
    creation_id = container.get("id")
    if not creation_id:
        raise RuntimeError(f"Instagram did not return creation container id: {container}")

    container_status = wait_for_instagram_container(creation_id, token, api_base)
    published = None
    publish_error = None
    for publish_attempt in range(1, 8):
        try:
            published = post_graph(
                f"{ig_user_id}/media_publish",
                token,
                {"creation_id": creation_id},
                base=api_base,
            )
            break
        except RuntimeError as exc:
            publish_error = exc
            if "9007" not in str(exc) and "Media ID is not available" not in str(exc):
                raise
            print(
                f"WAIT instagram media publish "
                f"{publish_attempt}/7 for container {creation_id}"
            )
            time.sleep(4)
    if published is None:
        raise RuntimeError(
            f"Instagram media_publish stayed unavailable: {publish_error}"
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

    media_payload = {
        "media_type": "VIDEO" if post.get("media_type") == "video" else "IMAGE",
        "text": caption_for(post, "threads"),
    }
    if post.get("media_type") == "video":
        media_payload["video_url"] = post["video_url"]
    else:
        media_payload["image_url"] = post["image_url"]

    container = post_graph(
        f"{threads_user_id}/threads",
        token,
        media_payload,
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

    is_video = post.get("media_type") == "video"
    media_method = "sendVideo" if is_video else "sendPhoto"
    media_key = "video" if is_video else "photo"
    media_payload = {
        "chat_id": chat_id,
        media_key: post["video_url"] if is_video else post["image_url"],
    }
    followup = None
    if len(caption) <= 1024:
        media_payload["caption"] = caption
        if "<" in caption and ">" in caption:
            media_payload["parse_mode"] = "HTML"
    else:
        media_payload["caption"] = caption[:1000].rstrip() + "…"
        followup = caption

    media_response = requests.post(
        f"{api_base}/{media_method}",
        data=media_payload,
        timeout=60,
    )
    try:
        media_body = media_response.json()
    except Exception:
        media_body = {"raw": media_response.text}
    if not media_response.ok or not media_body.get("ok"):
        raise RuntimeError(f"Telegram {media_method} failed: {media_body}")

    result = {media_key: media_body}
    if followup:
        message_data = {
            "chat_id": chat_id,
            "text": followup[:4096],
            "disable_web_page_preview": "true",
        }
        if "<" in followup and ">" in followup:
            message_data["parse_mode"] = "HTML"
        message_response = requests.post(
            f"{api_base}/sendMessage",
            data=message_data,
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

    if post.get("media_type") == "video":
        if post_mode == "MEDIA_UPLOAD":
            return post_json(
                tiktok_url("/v2/post/publish/inbox/video/init/"),
                token,
                {
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": post["video_url"],
                    }
                },
            )
        return post_json(
            tiktok_url("/v2/post/publish/video/init/"),
            token,
            {
                "post_info": {
                    "title": caption_for(post, "tiktok")[:2200],
                    "privacy_level": os.getenv(
                        "TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE"
                    ).strip()
                    or "PUBLIC_TO_EVERYONE",
                    "disable_comment": os.getenv(
                        "TIKTOK_DISABLE_COMMENT", "false"
                    ).lower()
                    in {"1", "true", "yes", "on"},
                    "brand_organic_toggle": True,
                    "is_aigc": bool(post.get("is_aigc", False)),
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "video_url": post["video_url"],
                },
            },
        )

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
            "photo_cover_index": 0,
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
    "facebook_story": publish_facebook_story,
    "instagram": publish_instagram,
    "instagram_story": publish_instagram,
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
        "facebook_story": ("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"),
        "instagram": ("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"),
        "instagram_story": ("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"),
        "threads": ("THREADS_USER_ID", "THREADS_ACCESS_TOKEN"),
        "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
        "tiktok": ("TIKTOK_ACCESS_TOKEN",),
    }.get(platform, ())
    return all(os.getenv(name, "").strip() for name in required)


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def is_due(post: dict, now: datetime, force: bool) -> bool:
    if post.get("status", "ready") not in {"ready", "approved"}:
        return False
    if force:
        return True
    scheduled = parse_dt(post["scheduled_at"])
    # Older generated story queues used timestamps without an explicit offset.
    # Treat them as UTC so comparisons with the aware `now` value stay valid.
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    return scheduled <= now


def latest_platform_publication(state: dict, platform: str) -> datetime | None:
    latest = None
    for post_state in state.get("published", {}).values():
        platform_state = post_state.get(platform) if isinstance(post_state, dict) else None
        if not isinstance(platform_state, dict):
            continue
        value = platform_state.get("published_at")
        if not value:
            continue
        try:
            published_at = parse_dt(value)
        except (TypeError, ValueError):
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        if latest is None or published_at > latest:
            latest = published_at
    return latest


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
    disabled_platforms = {
        item.strip()
        for item in os.getenv("DISABLED_PLATFORMS", "").split(",")
        if item.strip()
    }

    data = load_json(POSTS_FILE, {})
    posts = data.get("posts", [])
    state = load_json(STATE_FILE, {"published": {}})
    state.setdefault("published", {})

    now = datetime.now(timezone.utc).astimezone()
    min_interval_minutes = max(
        0, int(os.getenv("MIN_SUCCESS_INTERVAL_MINUTES", "0"))
    )
    platform_ready_at = {}
    for platform in PUBLISHERS:
        latest = latest_platform_publication(state, platform)
        platform_ready_at[platform] = (
            latest + timedelta(minutes=min_interval_minutes) if latest else None
        )

    def platform_interval_open(platform: str) -> bool:
        ready_at = platform_ready_at.get(platform)
        return args.force or ready_at is None or now >= ready_at
    selected = []
    max_posts_per_run = max(1, int(os.getenv("MAX_POSTS_PER_RUN", "1")))
    for post in posts:
        if args.post_id and post["id"] != args.post_id:
            continue
        if not is_due(post, now, args.force):
            continue
        post_state = state["published"].get(post["id"], {})
        actionable_platforms = [
            platform
            for platform in post.get("platforms", [])
            if platform in PUBLISHERS
            and platform not in disabled_platforms
            and (not platforms_filter or platform in platforms_filter)
            and platform_has_credentials(platform)
            and platform_interval_open(platform)
            and not post_state.get(platform)
        ]
        if not actionable_platforms:
            continue
        selected.append(post)
        if len(selected) >= max_posts_per_run:
            break

    if not selected:
        print("No due posts.")
        return 0

    published_count = 0
    skipped_count = 0
    failed = []
    attempted_platforms = set()

    for post in selected:
        post_state = state["published"].setdefault(post["id"], {})
        platforms = [p for p in post.get("platforms", []) if p in PUBLISHERS]
        if platforms_filter:
            platforms = [p for p in platforms if p in platforms_filter]
        platforms = [p for p in platforms if p not in disabled_platforms]

        for platform in platforms:
            if platform in attempted_platforms and not args.force:
                skipped_count += 1
                continue
            if not platform_interval_open(platform):
                skipped_count += 1
                continue
            if not platform_has_credentials(platform):
                warn(f"Skip not configured platform: {post['id']} -> {platform}")
                skipped_count += 1
                continue

            if post_state.get(platform) and not args.force:
                print(f"SKIP already published: {post['id']} -> {platform}")
                skipped_count += 1
                continue

            print(f"{'DRY ' if dry_run else ''}PUBLISH {post['id']} -> {platform}")
            attempted_platforms.add(platform)
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
            error("One or more publication attempts failed. Check tokens and permissions.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
