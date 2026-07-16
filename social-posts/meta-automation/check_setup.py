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


def main() -> int:
    load_env_file(ENV_FILE)

    page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()
    page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "").strip()
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    threads_user_id = os.getenv("THREADS_USER_ID", "").strip()
    threads_token = os.getenv("THREADS_ACCESS_TOKEN", "").strip()

    if not page_id:
        print("FACEBOOK_PAGE_ID is missing.")
        return 1

    if page_token:
        print("Checking Facebook Page token...")
        page = graph_get(
            page_id,
            page_token,
            {
                "fields": "id,name,instagram_business_account{id,username},connected_instagram_account{id,username}"
            },
        )
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
        if ig_token.startswith("IG"):
            ig = graph_get("me", ig_token, {"fields": "user_id,username,account_type"}, base="instagram")
        else:
            ig = graph_get(ig_user_id, ig_token, {"fields": "id,username,name"})
        print(json.dumps(ig, ensure_ascii=False, indent=2))
    else:
        print("INSTAGRAM_USER_ID or INSTAGRAM_ACCESS_TOKEN is empty; skipping Instagram check.")

    if threads_user_id and threads_token:
        print()
        print("Checking Threads token...")
        th = graph_get("me", threads_token, {"fields": "id,username"}, base="threads")
        print(json.dumps(th, ensure_ascii=False, indent=2))
    else:
        print("THREADS_USER_ID or THREADS_ACCESS_TOKEN is empty; skipping Threads check.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
