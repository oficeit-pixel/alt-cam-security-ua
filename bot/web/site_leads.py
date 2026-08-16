from html import escape
from datetime import datetime, timezone
from secrets import token_hex
from time import monotonic
from typing import Any

from aiohttp import web
from aiogram import Bot

from bot.config import get_settings


def _cors_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "Access-Control-Allow-Origin": settings.site_public_origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
    }


def _clean(value: Any, fallback: str = "Не вказано") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _rate_limited(request: web.Request, limit: int = 10, window: int = 60) -> bool:
    key = request.remote or "unknown"
    now = monotonic()
    attempts = [stamp for stamp in request.app["rate_limits"].get(key, []) if now - stamp < window]
    request.app["rate_limits"][key] = attempts
    if len(attempts) >= limit:
        return True
    attempts.append(now)
    return False


def _lead_text(payload: dict[str, Any]) -> str:
    lead_type = _clean(payload.get("type"))
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    quote = payload.get("quote") if isinstance(payload.get("quote"), dict) else {}
    message = _clean(payload.get("message"))
    source = _clean(payload.get("source"))

    lines = [
        "<b>Нова заявка з сайту ALT-CAM</b>",
        "",
        f"Тип: <b>{escape(lead_type)}</b>",
        f"Джерело: {escape(source)}",
    ]

    if client:
        lines.extend(
            [
                "",
                "<b>Клієнт</b>",
                f"Ім'я: <b>{escape(_clean(client.get('name')))}</b>",
                f"Телефон: <code>{escape(_clean(client.get('phone')))}</code>",
                f"Email: {escape(_clean(client.get('email')))}",
                f"Бажана дата: {escape(_clean(client.get('date')))}",
                f"Коментар: {escape(_clean(client.get('comment')))}",
            ]
        )

    if quote:
        lines.extend(
            [
                "",
                "<b>Розрахунок</b>",
                f"Напрямок: <b>{escape(_clean(quote.get('type')))}</b>",
                f"Сума: <b>{escape(_clean(quote.get('total')))} грн</b>",
                f"Знижка: {escape(_clean(quote.get('discount')))} грн",
                f"Завдаток: {escape(_clean(quote.get('deposit')))} грн",
            ]
        )

    lines.extend(["", "<b>Деталі з калькулятора</b>", f"<pre>{escape(message)}</pre>"])
    return "\n".join(lines)


async def site_lead_options(_: web.Request) -> web.Response:
    return web.Response(status=204, headers=_cors_headers())


async def site_lead(request: web.Request) -> web.Response:
    if _rate_limited(request):
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429, headers=_cors_headers())
    settings = get_settings()
    bot: Bot = request.app["bot"]
    try:
        payload = await request.json()
    except Exception:
        return web.json_response(
            {"ok": False, "error": "invalid_json"},
            status=400,
            headers=_cors_headers(),
        )

    text = _lead_text(payload)
    targets = [settings.admin_chat_id]
    if settings.site_lead_group_id and settings.site_lead_group_id not in targets:
        targets.append(settings.site_lead_group_id)

    for chat_id in targets:
        await bot.send_message(chat_id, text[:4096])

    return web.json_response({"ok": True}, headers=_cors_headers())


async def api_options(_: web.Request) -> web.Response:
    return web.Response(status=204, headers=_cors_headers())


async def catalog_prices(_: web.Request) -> web.Response:
    # Public prices are embedded in the signed-off catalog feed. This endpoint
    # remains stable for future manager overrides without exposing purchase data.
    return web.json_response({}, headers=_cors_headers())


async def analytics(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400, headers=_cors_headers())
    event = _clean(payload.get("event"), "unknown")[:64]
    request.app["logger"].info("catalog_event event=%s", event)
    return web.json_response({"ok": True}, headers=_cors_headers())


async def create_order(request: web.Request) -> web.Response:
    if _rate_limited(request):
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429, headers=_cors_headers())
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400, headers=_cors_headers())
    customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    name = _clean(customer.get("name"), "")[:120]
    phone = _clean(customer.get("phone"), "")[:40]
    if not name or not phone or not items or len(items) > 100:
        return web.json_response({"ok": False, "error": "invalid_order"}, status=422, headers=_cors_headers())

    order_number = f"WEB-{datetime.now(timezone.utc):%Y%m%d}-{token_hex(3).upper()}"
    lines = [
        f"<b>Нове замовлення {escape(order_number)}</b>", "",
        f"Клієнт: <b>{escape(name)}</b>",
        f"Телефон: <code>{escape(phone)}</code>",
        f"Місто: {escape(_clean(customer.get('city')))}", "", "<b>Позиції</b>",
    ]
    for index, item in enumerate(items[:100], 1):
        if not isinstance(item, dict):
            continue
        lines.append(f"{index}. {escape(_clean(item.get('name'))[:240])}")
    text = "\n".join(lines)[:4096]
    settings = get_settings()
    targets = [settings.admin_chat_id]
    if settings.site_lead_group_id and settings.site_lead_group_id not in targets:
        targets.append(settings.site_lead_group_id)
    bot: Bot = request.app["bot"]
    for chat_id in targets:
        await bot.send_message(chat_id, text)
    return web.json_response({"ok": True, "order_number": order_number}, headers=_cors_headers())


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "alt-cam-bot"})


async def start_site_lead_server(bot: Bot) -> web.AppRunner:
    settings = get_settings()
    app = web.Application()
    app["bot"] = bot
    app["rate_limits"] = {}
    import logging
    app["logger"] = logging.getLogger("altcam.catalog")
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_options("/site-lead", site_lead_options)
    app.router.add_post("/site-lead", site_lead)
    app.router.add_options("/api/{tail:.*}", api_options)
    app.router.add_get("/api/catalog/prices", catalog_prices)
    app.router.add_post("/api/analytics", analytics)
    app.router.add_post("/api/orders", create_order)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.http_host, settings.http_port)
    await site.start()
    return runner
