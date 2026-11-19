"""Opt-in Telegram delivery for hosts which sleep without inbound requests."""
import hashlib
import hmac
from urllib.parse import urlsplit

PATH = "/telegram/webhook"


def validate_url(url: str) -> str:
    # Dashboard copy/paste may add whitespace or a trailing path slash.
    # Do not silently repair a different host/path, credentials or query string.
    url = url.strip()
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.path not in (PATH, PATH + "/")
            or parsed.query or parsed.fragment or any(c.isspace() for c in url)):
        raise ValueError("TELEGRAM_WEBHOOK_URL must be an HTTPS URL ending in /telegram/webhook")
    return parsed._replace(path=PATH).geturl()


def webhook_secret(bot_token: str) -> str:
    if not bot_token:
        raise ValueError("Bot token is required")
    # Domain-separated HMAC; neither token nor derived secret is logged or stored.
    return hmac.new(bot_token.encode(), b"altcam-telegram-webhook-v1", hashlib.sha256).hexdigest()


def register_webhook(app, dispatcher, bot, url: str) -> None:
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    validate_url(url)
    SimpleRequestHandler(
        dispatcher=dispatcher, bot=bot,
        secret_token=webhook_secret(bot.token), handle_in_background=False,
    ).register(app, path=PATH)
    setup_application(app, dispatcher, bot=bot)


async def activate_webhook(bot, dispatcher, url: str) -> None:
    await bot.set_webhook(
        url=validate_url(url), secret_token=webhook_secret(bot.token),
        allowed_updates=dispatcher.resolve_used_update_types(),
        drop_pending_updates=False, max_connections=1,
    )
