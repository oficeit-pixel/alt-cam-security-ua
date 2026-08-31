import asyncio
from html import escape
from datetime import datetime, timedelta, timezone
from secrets import token_hex
from time import monotonic
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web
from aiogram import Bot
from sqlalchemy import select

from bot.db.base import SessionLocal
from bot.db.models import AdminAuditLog, AnalyticsEvent, PriceOverride, WebOrder
from bot.integrations.order_fulfillment import auto_create_order_drive_folder
from bot.web.shop_admin import register_shop_admin_routes

from bot.config import get_settings


def _cors_headers(request: web.Request | None = None) -> dict[str, str]:
    settings = get_settings()
    configured_origin = settings.site_public_origin.rstrip("/")
    allowed_origins = {
        configured_origin,
        "https://oficeit-pixel.github.io",
        "http://alt-cam.net.ua",
        "https://alt-cam.net.ua",
        "http://www.alt-cam.net.ua",
        "https://www.alt-cam.net.ua",
    }
    request_origin = (request.headers.get("Origin") if request else None) or ""
    response_origin = request_origin.rstrip("/") if request_origin.rstrip("/") in allowed_origins else configured_origin
    return {
        "Access-Control-Allow-Origin": response_origin,
        "Access-Control-Allow-Methods": "GET, POST, PATCH, PUT, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
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


async def _post_order_notifications(
    app: web.Application,
    *,
    order_number: str,
    customer: dict[str, str],
    delivery: dict[str, str],
    items: list[dict[str, Any]],
    subtotal: float,
) -> bool:
    settings = get_settings()
    if not settings.email_relay_url or not settings.email_relay_secret:
        app["logger"].warning(
            "order_notifications_not_configured order=%s", order_number
        )
        return False

    item_lines = [
        f"{index}. {item['name']} × {item['quantity']} — "
        f"{item['price'] * item['quantity']:.2f} ₴"
        for index, item in enumerate(items, 1)
    ]
    delivery_label = _clean(delivery.get("label") or delivery.get("type"), "Не вказано")
    city = _clean(delivery.get("city"), "Не вказано")
    place = _clean(delivery.get("place"), "")
    order_details = "\n".join(item_lines)
    email_text = "\n".join([
        f"Нове замовлення {order_number}",
        "",
        f"Клієнт: {customer['name']}",
        f"Телефон: {customer['phone']}",
        f"Email: {_clean(customer.get('email'), 'Не вказано')}",
        f"Місто: {city}",
        f"Доставка: {delivery_label}",
        f"Відділення / адреса: {place}",
        "",
        "Позиції:",
        order_details,
        "",
        f"Сума: {subtotal:.2f} ₴",
    ])
    payloads = [
        {
            "name": customer["name"],
            "phone": customer["phone"],
            "city": city,
            "type": "Замовлення з сайту",
            "object": order_number,
            "cameras": str(sum(int(item["quantity"]) for item in items)),
            "comment": email_text,
            "source": "Сайт / кошик",
        },
        {
            "kind": "email",
            "secret": settings.email_relay_secret,
            "recipient": settings.admin_web_email,
            "subject": f"Нове замовлення ALT-CAM {order_number}",
            "text": email_text,
        },
    ]

    timeout = ClientTimeout(total=20)
    sent = True
    async with ClientSession(timeout=timeout) as client:
        for index, payload in enumerate(payloads):
            channel = "sheets" if index == 0 else "email"
            try:
                async with client.post(settings.email_relay_url, json=payload) as response:
                    result = await response.json(content_type=None)
                    if response.status >= 400 or result.get("status") != "success":
                        raise RuntimeError(
                            f"relay_status={response.status} result={result.get('status')}"
                        )
            except Exception as exc:
                sent = False
                app["logger"].exception(
                    "order_notification_failed order=%s channel=%s error=%s",
                    order_number,
                    channel,
                    exc,
                )
            else:
                app["logger"].info(
                    "order_notification_sent order=%s channel=%s",
                    order_number,
                    channel,
                )
    return sent


async def _backfill_latest_order_notification(app: web.Application) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    async with SessionLocal() as session:
        order = await session.scalar(
            select(WebOrder)
            .where(WebOrder.created_at >= cutoff)
            .order_by(WebOrder.created_at.desc())
            .limit(1)
        )
        if order is None:
            return
        already_sent = await session.scalar(
            select(AdminAuditLog.id).where(
                AdminAuditLog.action == "order_notification_backfill",
                AdminAuditLog.entity_type == "web_order",
                AdminAuditLog.entity_id == order.order_number,
            )
        )
        if already_sent:
            return

        sent = await _post_order_notifications(
            app,
            order_number=order.order_number,
            customer=order.customer or {},
            delivery=order.delivery or {},
            items=order.items or [],
            subtotal=float(order.subtotal or 0),
        )
        if not sent:
            return
        session.add(
            AdminAuditLog(
                admin_email="system@alt-cam.net.ua",
                action="order_notification_backfill",
                entity_type="web_order",
                entity_id=order.order_number,
                details={"channels": ["sheets", "email"]},
            )
        )
        await session.commit()
        app["logger"].info("order_notification_backfilled order=%s", order.order_number)


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
    bot: Bot | None = request.app["bot"]
    try:
        payload = await request.json()
    except Exception:
        return web.json_response(
            {"ok": False, "error": "invalid_json"},
            status=400,
            headers=_cors_headers(),
        )

    text = _lead_text(payload)
    targets = [settings.admin_chat_id] if settings.admin_chat_id else []
    if settings.site_lead_group_id and settings.site_lead_group_id not in targets:
        targets.append(settings.site_lead_group_id)

    for chat_id in targets:
        if bot:
            await bot.send_message(chat_id, text[:4096])

    return web.json_response({"ok": True}, headers=_cors_headers())


async def api_options(_: web.Request) -> web.Response:
    return web.Response(status=204, headers=_cors_headers())


async def catalog_prices(_: web.Request) -> web.Response:
    async with SessionLocal() as session:
        rows = (await session.scalars(select(PriceOverride).where(PriceOverride.enabled.is_(True)))).all()
    return web.json_response({row.product_id: float(row.price_uah) for row in rows}, headers=_cors_headers())


async def analytics(request: web.Request) -> web.Response:
    if _rate_limited(request, limit=120, window=60):
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429, headers=_cors_headers())
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400, headers=_cors_headers())
    event = _clean(payload.get("event"), "unknown")[:64]
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if len(str(data)) > 4096:
        data = {}
    async with SessionLocal() as session:
        session.add(AnalyticsEvent(event=event, session_id=_clean(payload.get("session_id"), "")[:128] or None, page=_clean(payload.get("page"), "")[:255] or None, data=data))
        await session.commit()
    request.app["logger"].info("catalog_event event=%s", event)
    return web.json_response({"ok": True}, headers=_cors_headers())


async def create_order(request: web.Request) -> web.Response:
    if _rate_limited(request):
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429, headers=_cors_headers())
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400, headers=_cors_headers())
    raw_customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    name = _clean(raw_customer.get("name"), "")[:120]
    phone = _clean(raw_customer.get("phone"), "")[:40]
    if not name or not phone or not items or len(items) > 100:
        return web.json_response({"ok": False, "error": "invalid_order"}, status=422, headers=_cors_headers())

    raw_delivery = payload.get("delivery") if isinstance(payload.get("delivery"), dict) else {}
    telegram_username = _clean(raw_customer.get("telegram"), "").lstrip("@")[:64]
    customer = {"name": name, "phone": phone, "email": _clean(raw_customer.get("email"), "")[:180]}
    delivery = {key: _clean(raw_delivery.get(key), "")[:500] for key in ("type", "label", "city", "city_ref", "place", "place_ref", "comment")}
    delivery_type = str(delivery.get("type", ""))
    if delivery_type not in {"branch", "locker", "courier", "pickup"}:
        return web.json_response({"ok": False, "error": "invalid_delivery"}, status=422, headers=_cors_headers())
    order_number = f"WEB-{datetime.now(timezone.utc):%Y%m%d}-{token_hex(3).upper()}"
    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            item_price = max(0, min(float(item.get("price") or 0), 10_000_000))
            item_quantity = max(1, min(int(item.get("quantity") or 1), 100))
        except (TypeError, ValueError, OverflowError):
            continue
        normalized_items.append({
            "id": _clean(item.get("id"), "")[:96], "type": _clean(item.get("type"), "product")[:24],
            "name": _clean(item.get("name"), "")[:240], "price": item_price, "quantity": item_quantity,
        })
    if not normalized_items:
        return web.json_response({"ok": False, "error": "invalid_order"}, status=422, headers=_cors_headers())
    subtotal = sum(item["price"] * item["quantity"] for item in normalized_items)
    async with SessionLocal() as session:
        order = WebOrder(order_number=order_number, customer=customer, delivery=delivery, items=normalized_items, subtotal=subtotal, status="new", telegram_username=telegram_username or None)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        order_id = order.id
    drive_task = asyncio.create_task(auto_create_order_drive_folder(order_id))
    drive_task.add_done_callback(lambda task: request.app["logger"].error("drive_folder_auto_create_failed order=%s error=%s", order_number, task.exception()) if not task.cancelled() and task.exception() else None)
    lines = [
        f"<b>Нове замовлення {escape(order_number)}</b>", "",
        f"Клієнт: <b>{escape(name)}</b>",
        f"Телефон: <code>{escape(phone)}</code>",
        f"Email: {escape(_clean(customer.get('email')))}",
        f"Доставка: {escape(_clean(delivery.get('label') or delivery_type))}", "", "<b>Позиції</b>",
    ]
    for index, item in enumerate(normalized_items, 1):
        if not isinstance(item, dict):
            continue
        lines.append(f"{index}. {escape(_clean(item.get('name'))[:220])} × {max(1, int(item.get('quantity') or 1))}")
    text = "\n".join(lines)[:4096]
    settings = get_settings()
    targets = [settings.admin_chat_id] if settings.admin_chat_id else []
    if settings.site_lead_group_id and settings.site_lead_group_id not in targets:
        targets.append(settings.site_lead_group_id)
    bot: Bot | None = request.app["bot"]
    for chat_id in targets:
        if bot:
            await bot.send_message(chat_id, text)
    await _post_order_notifications(
        request.app,
        order_number=order_number,
        customer=customer,
        delivery=delivery,
        items=normalized_items,
        subtotal=subtotal,
    )
    return web.json_response({"ok": True, "order_number": order_number}, headers=_cors_headers())


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "alt-cam-bot"})


@web.middleware
async def cors_middleware(request: web.Request, handler):
    response = await handler(request)
    if request.path.startswith("/api/") or request.path == "/site-lead":
        for key, value in _cors_headers(request).items():
            response.headers[key] = value
    return response


async def start_site_lead_server(bot: Bot | None) -> web.AppRunner:
    settings = get_settings()
    app = web.Application(middlewares=[cors_middleware])
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
    register_shop_admin_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.http_host, settings.http_port)
    await site.start()
    await _backfill_latest_order_notification(app)
    return runner
