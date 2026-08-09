from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = Path(os.getenv("SOCIAL_STATE_FILE", "social-posts/meta-automation/august-priority-state.json"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete previously published Telegram message using saved publisher state.")
    parser.add_argument("--post-id", required=True)
    parser.add_argument("--platform", default="telegram")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN is empty; skip delete.")
        return 0

    state_path = STATE_FILE if STATE_FILE.is_absolute() else ROOT / STATE_FILE
    state = load_json(state_path)
    platform_state = state.get("published", {}).get(args.post_id, {}).get(args.platform)
    if not platform_state:
        print(f"No saved {args.platform} state for {args.post_id}; skip delete.")
        return 0

    result = platform_state.get("result", {})
    message = (
        result.get("photo", {}).get("result")
        or result.get("video", {}).get("result")
        or result.get("message", {}).get("result")
    )
    if not message:
        print(f"No Telegram message payload for {args.post_id}; skip delete.")
        return 0

    chat = message.get("chat") or {}
    chat_id = chat.get("id") or os.getenv("TELEGRAM_CHAT_ID", "").strip()
    message_id = message.get("message_id")
    if not chat_id or not message_id:
        print(f"Missing chat_id/message_id for {args.post_id}; skip delete.")
        return 0

    response = requests.post(
        f"https://api.telegram.org/bot{token}/deleteMessage",
        data={"chat_id": chat_id, "message_id": message_id},
        timeout=60,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    if not response.ok or not body.get("ok"):
        print(f"Telegram delete failed for {args.post_id}: {body}")
        return 0

    print(f"Deleted Telegram message for {args.post_id}: chat_id={chat_id} message_id={message_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
