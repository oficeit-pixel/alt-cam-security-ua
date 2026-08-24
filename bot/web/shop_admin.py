import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from secrets import compare_digest
from typing import Any

from aiohttp import ClientSession, web
from sqlalchemy import desc, func, select

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import AnalyticsEvent, PriceOverride, WebOrder

ORDER_STATUSES = {"new", "confirmed", "awaiting_payment", "packing", "shipped", "completed", "canceled"}


def _secret() -> bytes:
    settings = get_settings()
    return (settings.admin_session_secret or settings.bot_token).encode()


def create_admin_token(email: str, ttl: int = 8 * 3600) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"email": email, "exp": int(time.time()) + ttl}, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_admin_token(token: str) -> bool:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not compare_digest(signature, expected):
            return False
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        settings = get_settings()
        return data.get("email", "").casefold() == settings.admin_web_email.casefold() and int(data.get("exp", 0)) > time.time()
    except Exception:
        return False


def require_admin(request: web.Request) -> None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not verify_admin_token(header[7:]):
        raise web.HTTPUnauthorized(text=json.dumps({"ok": False, "error": "unauthorized"}), content_type="application/json")


def serialize_order(order: WebOrder) -> dict[str, Any]:
    return {
        "id": order.id, "order_number": order.order_number, "customer": order.customer,
        "delivery": order.delivery, "items": order.items, "subtotal": float(order.subtotal or 0),
        "status": order.status, "manager_note": order.manager_note,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


async def admin_login(request: web.Request) -> web.Response:
    now = time.monotonic()
    key = f"admin-login:{request.remote or 'unknown'}"
    attempts = [stamp for stamp in request.app["rate_limits"].get(key, []) if now - stamp < 300]
    if len(attempts) >= 8:
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429)
    attempts.append(now)
    request.app["rate_limits"][key] = attempts
    settings = get_settings()
    payload = await request.json()
    email = str(payload.get("email", "")).strip().casefold()
    password = str(payload.get("password", ""))
    configured = settings.admin_web_password or ""
    if not configured or not compare_digest(email, settings.admin_web_email.casefold()) or not compare_digest(password, configured):
        await asyncio_sleep()
        return web.json_response({"ok": False, "error": "invalid_credentials"}, status=401)
    return web.json_response({"ok": True, "token": create_admin_token(settings.admin_web_email), "email": settings.admin_web_email})


async def asyncio_sleep() -> None:
    import asyncio
    await asyncio.sleep(0.35)


async def admin_me(request: web.Request) -> web.Response:
    require_admin(request)
    return web.json_response({"ok": True, "email": get_settings().admin_web_email})


async def dashboard(request: web.Request) -> web.Response:
    require_admin(request)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    async with SessionLocal() as session:
        order_count = await session.scalar(select(func.count()).select_from(WebOrder)) or 0
        new_count = await session.scalar(select(func.count()).select_from(WebOrder).where(WebOrder.status == "new")) or 0
        revenue = await session.scalar(select(func.coalesce(func.sum(WebOrder.subtotal), 0)).where(WebOrder.status != "canceled")) or 0
        events = await session.scalar(select(func.count()).select_from(AnalyticsEvent).where(AnalyticsEvent.created_at >= since)) or 0
        popular = (await session.execute(
            select(AnalyticsEvent.data["id"].astext.label("product_id"), func.count().label("views"))
            .where(AnalyticsEvent.event.in_(["product_view", "price_request_started", "add_to_cart"]), AnalyticsEvent.data.has_key("id"))
            .group_by("product_id").order_by(desc("views")).limit(12)
        )).all()
    return web.json_response({"orders": order_count, "new_orders": new_count, "revenue": float(revenue), "events_30d": events, "popular": [{"product_id": row.product_id, "views": row.views} for row in popular]})


async def list_orders(request: web.Request) -> web.Response:
    require_admin(request)
    status = request.query.get("status")
    async with SessionLocal() as session:
        query = select(WebOrder).order_by(WebOrder.created_at.desc()).limit(250)
        if status in ORDER_STATUSES:
            query = query.where(WebOrder.status == status)
        orders = (await session.scalars(query)).all()
    return web.json_response({"orders": [serialize_order(order) for order in orders]})


async def update_order(request: web.Request) -> web.Response:
    require_admin(request)
    payload = await request.json()
    async with SessionLocal() as session:
        order = await session.get(WebOrder, int(request.match_info["order_id"]))
        if not order:
            raise web.HTTPNotFound()
        status = payload.get("status")
        if status is not None:
            if status not in ORDER_STATUSES:
                return web.json_response({"ok": False, "error": "invalid_status"}, status=422)
            order.status = status
        if "manager_note" in payload:
            order.manager_note = str(payload.get("manager_note") or "")[:2000]
        await session.commit()
        await session.refresh(order)
    return web.json_response({"ok": True, "order": serialize_order(order)})


async def list_prices(request: web.Request) -> web.Response:
    require_admin(request)
    async with SessionLocal() as session:
        rows = (await session.scalars(select(PriceOverride).order_by(PriceOverride.product_id))).all()
    return web.json_response({"prices": [{"product_id": row.product_id, "price": float(row.price_uah), "enabled": row.enabled} for row in rows]})


async def save_price(request: web.Request) -> web.Response:
    require_admin(request)
    payload = await request.json()
    product_id = str(payload.get("product_id", ""))[:96]
    try:
        price = Decimal(str(payload.get("price")))
    except Exception:
        price = Decimal("0")
    if not product_id or price <= 0:
        return web.json_response({"ok": False, "error": "invalid_price"}, status=422)
    async with SessionLocal() as session:
        row = await session.get(PriceOverride, product_id)
        if row is None:
            row = PriceOverride(product_id=product_id, price_uah=price)
            session.add(row)
        else:
            row.price_uah = price
        row.enabled = bool(payload.get("enabled", True))
        await session.commit()
    return web.json_response({"ok": True})


async def public_prices(_: web.Request) -> web.Response:
    async with SessionLocal() as session:
        rows = (await session.scalars(select(PriceOverride).where(PriceOverride.enabled.is_(True)))).all()
    return web.json_response({row.product_id: float(row.price_uah) for row in rows})


async def nova_poshta(request: web.Request) -> web.Response:
    settings = get_settings()
    if not settings.nova_poshta_api_key:
        return web.json_response({"ok": False, "error": "not_configured"}, status=503)
    kind = request.match_info["kind"]
    query = request.query.get("q", "").strip()[:120]
    city_ref = request.query.get("city_ref", "")[:64]
    if kind == "cities":
        model, method, props = "Address", "searchSettlements", {"CityName": query, "Limit": "30", "Page": "1"}
    elif kind == "warehouses" and city_ref:
        model, method, props = "Address", "getWarehouses", {"SettlementRef": city_ref, "FindByString": query, "Limit": "100"}
    else:
        return web.json_response({"ok": False, "error": "invalid_request"}, status=422)
    body = {"apiKey": settings.nova_poshta_api_key, "modelName": model, "calledMethod": method, "methodProperties": props}
    async with ClientSession() as client:
        async with client.post("https://api.novaposhta.ua/v2.0/json/", json=body, timeout=12) as response:
            data = await response.json()
    return web.json_response(data)


def register_shop_admin_routes(app: web.Application) -> None:
    app.router.add_post("/api/admin/login", admin_login)
    app.router.add_get("/api/admin/me", admin_me)
    app.router.add_get("/api/admin/dashboard", dashboard)
    app.router.add_get("/api/admin/orders", list_orders)
    app.router.add_patch("/api/admin/orders/{order_id}", update_order)
    app.router.add_get("/api/admin/prices", list_prices)
    app.router.add_put("/api/admin/prices", save_price)
    app.router.add_get("/api/nova-poshta/{kind}", nova_poshta)
