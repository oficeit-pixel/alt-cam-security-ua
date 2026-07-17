import json
import os
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
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


def graph_url(path: str) -> str:
    version = os.getenv("META_GRAPH_VERSION", "v21.0").strip().lstrip("/")
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


def github_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def warn(message: str) -> None:
    print(f"::warning::{github_escape(message)}")


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


def graph_get(path: str, token: str, params: dict | None = None, *, base: str = "facebook") -> dict:
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


def tiktok_post(path: str, token: str, payload: dict | None = None) -> dict:
    response = requests.post(
        tiktok_url(path),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json=payload or {},
        timeout=60,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    if not response.ok:
        raise RuntimeError(f"TikTok API error {response.status_code} for {path}: {body}")
    return body


def main() -> int:
    load_env_file(ENV_FILE)
    failures: list[str] = []

    page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()
    page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "").strip()
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    threads_user_id = os.getenv("THREADS_USER_ID", "").strip()
    threads_token = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    tiktok_token = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()

    if not page_id:
        print("FACEBOOK_PAGE_ID is missing.")
        return 1

    if page_token:
        print("Checking Facebook Page token...")
        try:
            page = graph_get(
                page_id,
                page_token,
                {
                    "fields": "id,name,instagram_business_account{id,username},connected_instagram_account{id,username}"
                },
            )
        except Exception as exc:
            failures.append(f"Facebook Page token check failed: {exc}")
            print(f"Facebook Page token check failed: {exc}")
            print("Use a Meta Business system user token for FACEBOOK_PAGE_ACCESS_TOKEN.")
        else:
            print(json.dumps(page, ensure_ascii=False, indent=2))
            ig = page.get("instagram_business_account") or page.get("connected_instagram_account")
            if ig and not ig_user_id:
                print()
                print(f"Suggested INSTAGRAM_USER_ID={ig.get('id')}")
    else:
        print("FACEBOOK_PAGE_ACCESS_TOKEN is empty; skipping Page check.")

    if ig_user_id and ig_token:
        print()
        print("Checking Instagram token...")
        try:
            if ig_token.startswith("IG"):
                ig = graph_get("me", ig_token, {"fields": "user_id,username,account_type"}, base="instagram")
            else:
                ig = graph_get(ig_user_id, ig_token, {"fields": "id,username,name"})
        except Exception as exc:
            failures.append(f"Instagram token check failed: {exc}")
            print(f"Instagram token check failed: {exc}")
        else:
            print(json.dumps(ig, ensure_ascii=False, indent=2))
    else:
        print("INSTAGRAM_USER_ID or INSTAGRAM_ACCESS_TOKEN is empty; skipping Instagram check.")

    if threads_user_id and threads_token:
        print()
        print("Checking Threads token...")
        try:
            th = graph_get("me", threads_token, {"fields": "id,username"}, base="threads")
        except Exception as exc:
            failures.append(f"Threads token check failed: {exc}")
            print(f"Threads token check failed: {exc}")
        else:
            print(json.dumps(th, ensure_ascii=False, indent=2))
    else:
        print("THREADS_USER_ID or THREADS_ACCESS_TOKEN is empty; skipping Threads check.")

    if telegram_bot_token and telegram_chat_id:
        print()
        print("Checking Telegram bot token...")
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{telegram_bot_token}/getMe",
                timeout=60,
            )
            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text}
            if not response.ok or not body.get("ok"):
                raise RuntimeError(f"Telegram getMe failed: {body}")
        except Exception as exc:
            failures.append(f"Telegram token check failed: {exc}")
            print(f"Telegram token check failed: {exc}")
        else:
            print(json.dumps(body, ensure_ascii=False, indent=2))
            print(f"Telegram target chat: {telegram_chat_id}")
    else:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty; skipping Telegram check.")

    if tiktok_token:
        print()
        print("Checking TikTok Content Posting token...")
        try:
            creator = tiktok_post("/v2/post/publish/creator_info/query/", tiktok_token)
        except Exception as exc:
            failures.append(f"TikTok token check failed: {exc}")
            print(f"TikTok token check failed: {exc}")
        else:
            print(json.dumps(creator, ensure_ascii=False, indent=2))
    else:
        print("TIKTOK_ACCESS_TOKEN is empty; skipping TikTok check.")

    if failures:
        print()
        print("Setup check finished with warnings:")
        for failure in failures:
            print(f"- {failure}")
            warn(failure)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
