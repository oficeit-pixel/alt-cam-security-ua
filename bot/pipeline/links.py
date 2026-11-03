"""Signed Telegram deep links (t.me/<bot>?start=...) binding a site request to a chat."""
from __future__ import annotations

import hashlib
import hmac
import re

from bot.config import get_settings

PARAM_PATTERN = re.compile(r"^(?P<kind>[ol])(?P<id>\d{1,12})_(?P<sig>[A-Za-z0-9]{10})$")


def _secret() -> bytes:
    settings = get_settings()
    secret = settings.pipeline_link_secret or settings.admin_session_secret or settings.bot_token or ""
    return secret.encode()


def _sign(kind: str, object_id: int) -> str:
    digest = hmac.new(_secret(), f"{kind}{object_id}".encode(), hashlib.sha256).hexdigest()
    return digest[:10]


def start_param(kind: str, object_id: int) -> str:
    """kind: 'o' = web order, 'l' = site lead. Result fits Telegram's 64-char [A-Za-z0-9_-] limit."""
    if kind not in {"o", "l"}:
        raise ValueError("invalid_kind")
    return f"{kind}{int(object_id)}_{_sign(kind, int(object_id))}"


def parse_start_param(value: str | None) -> tuple[str, int] | None:
    match = PARAM_PATTERN.match(value or "")
    if not match or not _secret():
        return None
    kind, object_id = match["kind"], int(match["id"])
    if not hmac.compare_digest(match["sig"], _sign(kind, object_id)):
        return None
    return kind, object_id


def bot_link(kind: str, object_id: int) -> str:
    return f"https://t.me/{get_settings().bot_username}?start={start_param(kind, object_id)}"
