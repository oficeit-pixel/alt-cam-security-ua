"""Private Telegram Mini App checkout identity. Never trust a phone or a URL alone."""
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram.utils.web_app import safe_parse_webapp_init_data


def launch_url(url: str, inquiry_id: int) -> str | None:
    p = urlsplit(url)
    if p.scheme != "https" or p.netloc != "alt-cam.net.ua" or p.path != "/catalog.html":
        return None
    pairs = [(k, v) for k, v in parse_qsl(p.query) if k == "cart"]
    pairs.append(("consultation", str(inquiry_id)))
    if p.fragment == "services":
        pairs.append(("section", "services"))
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(pairs), ""))


def verified_context(value, token: str | None, now=None):
    if not isinstance(value, dict) or not token:
        return None
    data, inquiry_id = value.get("init"), value.get("inquiry")
    if not isinstance(data, str) or len(data) > 8192 or not isinstance(inquiry_id, str) or not inquiry_id.isascii() or not inquiry_id.isdigit() or len(inquiry_id) > 10:
        return None
    try:
        auth = safe_parse_webapp_init_data(token, data)
        age = (time.time() if now is None else now) - auth.auth_date.timestamp()
        if auth.user and not auth.user.is_bot and -30 <= age <= 3600:
            return int(inquiry_id), auth.user.id
    except (ValueError, TypeError, KeyError, OverflowError, OSError):
        pass
    return None
