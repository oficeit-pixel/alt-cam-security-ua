import base64
import hashlib
import hmac
import json
import os
import smtplib
import time
from asyncio import to_thread
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.message import EmailMessage
from secrets import compare_digest, randbelow, token_urlsafe
from typing import Any

from aiohttp import ClientSession, web
from sqlalchemy import String, cast, desc, func, or_, select, update

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import AdminAuditLog, AdminAuthToken, AdminUser, AnalyticsEvent, PriceOverride, WebOrder

ORDER_STATUSES = {
    "new", "clarification", "ordered_from_supplier", "waiting_tracking",
    "shipped", "in_transit", "arrived", "received", "completed",
    "problem", "canceled",
}
ATTENTION_STATUSES = {"new", "arrived", "problem"}
TRACKING_PROVIDERS = {"nova_poshta", "ukrposhta", "other"}
ROLES = {"chief", "manager"}


def _secret() -> bytes:
    settings = get_settings()
    return (settings.admin_session_secret or settings.bot_token).encode()


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(rounds))
        return compare_digest(base64.urlsafe_b64encode(actual).decode(), expected)
    except Exception:
        return False


def create_admin_token(user: AdminUser, ttl: int = 8 * 3600) -> str:
    password_version = int(user.password_changed_at.timestamp()) if user.password_changed_at else 0
    body = {"uid": user.id, "email": user.email, "role": user.role, "pwd": password_version, "exp": int(time.time()) + ttl}
    payload = base64.urlsafe_b64encode(json.dumps(body, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def decode_admin_token(token: str) -> dict[str, Any] | None:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not compare_digest(signature, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return data if int(data.get("exp", 0)) > time.time() else None
    except Exception:
        return None


def _signed_payload(data: dict[str, Any]) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def _decode_signed_payload(token: str) -> dict[str, Any] | None:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not compare_digest(signature, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return data if int(data.get("exp", 0)) > time.time() else None
    except Exception:
        return None


def _valid_password(password: str) -> bool:
    return len(password) >= 12 and any(c.islower() for c in password) and any(c.isupper() for c in password) and any(c.isdigit() for c in password)


def _verify_captcha(token: str, answer: str) -> bool:
    data = _decode_signed_payload(token)
    return bool(data and data.get("kind") == "captcha" and compare_digest(str(data.get("answer")), str(answer).strip()))


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def _issue_auth_token(session, admin_id: int, purpose: str, ttl_minutes: int) -> str:
    await session.execute(
        update(AdminAuthToken)
        .where(AdminAuthToken.admin_id == admin_id, AdminAuthToken.purpose == purpose, AdminAuthToken.used_at.is_(None))
        .values(used_at=datetime.now(timezone.utc))
    )
    raw_token = token_urlsafe(32)
    session.add(AdminAuthToken(
        admin_id=admin_id,
        purpose=purpose,
        token_hash=_token_hash(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
    ))
    return raw_token


async def _consume_auth_token(session, raw_token: str, purpose: str) -> tuple[AdminAuthToken, AdminUser] | None:
    token_row = await session.scalar(select(AdminAuthToken).where(
        AdminAuthToken.token_hash == _token_hash(raw_token),
        AdminAuthToken.purpose == purpose,
        AdminAuthToken.used_at.is_(None),
        AdminAuthToken.expires_at > datetime.now(timezone.utc),
    ))
    if not token_row:
        return None
    user = await session.get(AdminUser, token_row.admin_id)
    return (token_row, user) if user else None


def _send_email_sync(recipient: str, subject: str, text: str) -> None:
    settings = get_settings()
    if not settings.smtp_password:
        raise RuntimeError("smtp_not_configured")
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
        client.starttls()
        client.login(settings.smtp_user, settings.smtp_password)
        client.send_message(message)


async def _send_email(recipient: str, subject: str, text: str) -> None:
    await to_thread(_send_email_sync, recipient, subject, text)


async def current_admin(request: web.Request, chief_only: bool = False) -> AdminUser:
    header = request.headers.get("Authorization", "")
    data = decode_admin_token(header[7:]) if header.startswith("Bearer ") else None
    if not data:
        raise web.HTTPUnauthorized(text=json.dumps({"ok": False, "error": "unauthorized"}), content_type="application/json")
    async with SessionLocal() as session:
        user = await session.get(AdminUser, int(data.get("uid", 0)))
        password_version = int(user.password_changed_at.timestamp()) if user and user.password_changed_at else 0
        if not user or not user.active or user.email.casefold() != str(data.get("email", "")).casefold() or password_version != int(data.get("pwd", 0)):
            raise web.HTTPUnauthorized(text=json.dumps({"ok": False, "error": "unauthorized"}), content_type="application/json")
        if chief_only and user.role != "chief":
            raise web.HTTPForbidden(text=json.dumps({"ok": False, "error": "chief_required"}), content_type="application/json")
        session.expunge(user)
        return user


async def audit(session, user: AdminUser, request: web.Request, action: str, entity_type: str | None = None, entity_id: str | None = None, details: dict | None = None) -> None:
    session.add(AdminAuditLog(admin_id=user.id, admin_email=user.email, action=action, entity_type=entity_type, entity_id=entity_id, details=details or {}, ip_address=request.remote))


def serialize_order(order: WebOrder) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer": order.customer or {},
        "delivery": order.delivery or {},
        "items": order.items or [],
        "subtotal": float(order.subtotal or 0),
        "status": order.status,
        "manager_note": order.manager_note,
        "tracking_number": order.tracking_number,
        "tracking_provider": order.tracking_provider,
        "telegram_username": order.telegram_username,
        "drive_folder_url": order.drive_folder_url,
        "supplier_order_number": order.supplier_order_number,
        "problem_note": order.problem_note,
        "assigned_admin_id": order.assigned_admin_id,
        "status_history": order.status_history or [],
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


async def admin_captcha(_: web.Request) -> web.Response:
    left, right = randbelow(8) + 2, randbelow(8) + 2
    token = _signed_payload({"kind": "captcha", "answer": str(left + right), "exp": int(time.time()) + 600, "nonce": token_urlsafe(8)})
    return web.json_response({"ok": True, "question": f"{left} + {right} = ?", "token": token})


async def admin_register(request: web.Request) -> web.Response:
    if _rate_limit_auth(request, "register", 5, 3600):
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429)
    settings = get_settings()
    if not settings.smtp_password:
        return web.json_response({"ok": False, "error": "email_not_configured"}, status=503)
    payload = await request.json()
    email = str(payload.get("email", "")).strip().casefold()[:180]
    name = str(payload.get("name", "")).strip()[:120]
    password = str(payload.get("password", ""))
    if not _verify_captcha(str(payload.get("captcha_token", "")), str(payload.get("captcha_answer", ""))):
        return web.json_response({"ok": False, "error": "invalid_captcha"}, status=422)
    if "@" not in email or not name or not _valid_password(password):
        return web.json_response({"ok": False, "error": "invalid_registration"}, status=422)
    async with SessionLocal() as session:
        active_count = await session.scalar(select(func.count()).select_from(AdminUser).where(AdminUser.active.is_(True))) or 0
        if active_count >= 4:
            return web.json_response({"ok": False, "error": "admin_limit"}, status=409)
        user = await session.scalar(select(AdminUser).where(func.lower(AdminUser.email) == email))
        if user and user.email_verified_at:
            return web.json_response({"ok": False, "error": "email_exists"}, status=409)
        if user is None:
            user = AdminUser(email=email, name=name, password_hash=hash_password(password), role="manager", active=False)
            session.add(user)
            await session.flush()
        else:
            user.name = name
            user.password_hash = hash_password(password)
            user.role = "manager"
            user.active = False
        raw_token = await _issue_auth_token(session, user.id, "verify_email", 60)
        await session.commit()
    verification_url = f"{settings.admin_site_url}?verify={raw_token}"
    try:
        await _send_email(email, "Підтвердження реєстрації ALT-CAM", f"Вітаємо, {name}!\n\nПідтвердьте email адміністратора протягом 60 хвилин:\n{verification_url}\n\nЯкщо ви не реєструвалися, проігноруйте лист.")
    except Exception:
        return web.json_response({"ok": False, "error": "email_delivery_failed"}, status=503)
    return web.json_response({"ok": True, "message": "verification_sent"}, status=201)


async def admin_verify_email(request: web.Request) -> web.Response:
    payload = await request.json()
    async with SessionLocal() as session:
        result = await _consume_auth_token(session, str(payload.get("token", "")), "verify_email")
        if not result:
            return web.json_response({"ok": False, "error": "invalid_or_expired_token"}, status=422)
        token_row, user = result
        active_count = await session.scalar(select(func.count()).select_from(AdminUser).where(AdminUser.active.is_(True), AdminUser.id != user.id)) or 0
        if active_count >= 4:
            return web.json_response({"ok": False, "error": "admin_limit"}, status=409)
        now = datetime.now(timezone.utc)
        user.email_verified_at = now
        user.active = True
        token_row.used_at = now
        session.add(AdminAuditLog(admin_id=user.id, admin_email=user.email, action="email_verified", entity_type="admin", entity_id=str(user.id), details={}, ip_address=request.remote))
        await session.commit()
    return web.json_response({"ok": True})


async def admin_request_reset(request: web.Request) -> web.Response:
    if _rate_limit_auth(request, "reset", 5, 3600):
        return web.json_response({"ok": True})
    settings = get_settings()
    payload = await request.json()
    email = str(payload.get("email", "")).strip().casefold()[:180]
    async with SessionLocal() as session:
        user = await session.scalar(select(AdminUser).where(func.lower(AdminUser.email) == email, AdminUser.email_verified_at.is_not(None)))
        if not user or not user.active or not settings.smtp_password:
            return web.json_response({"ok": True})
        raw_token = await _issue_auth_token(session, user.id, "reset_password", 30)
        await session.commit()
    reset_url = f"{settings.admin_site_url}?reset={raw_token}"
    try:
        await _send_email(email, "Відновлення пароля ALT-CAM", f"Для створення нового пароля відкрийте посилання протягом 30 хвилин:\n{reset_url}\n\nЯкщо ви не запитували відновлення, проігноруйте лист.")
    except Exception:
        pass
    return web.json_response({"ok": True})


async def admin_reset_password(request: web.Request) -> web.Response:
    payload = await request.json()
    password = str(payload.get("password", ""))
    if not _valid_password(password):
        return web.json_response({"ok": False, "error": "weak_password"}, status=422)
    async with SessionLocal() as session:
        result = await _consume_auth_token(session, str(payload.get("token", "")), "reset_password")
        if not result:
            return web.json_response({"ok": False, "error": "invalid_or_expired_token"}, status=422)
        token_row, user = result
        now = datetime.now(timezone.utc)
        user.password_hash = hash_password(password)
        user.password_changed_at = now
        token_row.used_at = now
        session.add(AdminAuditLog(admin_id=user.id, admin_email=user.email, action="password_reset", entity_type="admin", entity_id=str(user.id), details={}, ip_address=request.remote))
        await session.commit()
    return web.json_response({"ok": True})


async def admin_change_password(request: web.Request) -> web.Response:
    current = await current_admin(request)
    payload = await request.json()
    old_password, new_password = str(payload.get("current_password", "")), str(payload.get("new_password", ""))
    if not _valid_password(new_password):
        return web.json_response({"ok": False, "error": "weak_password"}, status=422)
    async with SessionLocal() as session:
        user = await session.get(AdminUser, current.id)
        if not user or not verify_password(old_password, user.password_hash):
            return web.json_response({"ok": False, "error": "invalid_current_password"}, status=422)
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await audit(session, user, request, "password_changed", "admin", str(user.id))
        await session.commit()
    return web.json_response({"ok": True})


def _rate_limit_auth(request: web.Request, action: str, limit: int, window: int) -> bool:
    now = time.monotonic()
    key = f"admin-{action}:{request.remote or 'unknown'}"
    attempts = [stamp for stamp in request.app["rate_limits"].get(key, []) if now - stamp < window]
    request.app["rate_limits"][key] = attempts
    if len(attempts) >= limit:
        return True
    attempts.append(now)
    return False


async def admin_login(request: web.Request) -> web.Response:
    now = time.monotonic()
    key = f"admin-login:{request.remote or 'unknown'}"
    attempts = [stamp for stamp in request.app["rate_limits"].get(key, []) if now - stamp < 300]
    if len(attempts) >= 8:
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429)
    attempts.append(now)
    request.app["rate_limits"][key] = attempts
    payload = await request.json()
    email, password = str(payload.get("email", "")).strip().casefold(), str(payload.get("password", ""))
    settings = get_settings()
    async with SessionLocal() as session:
        user = await session.scalar(select(AdminUser).where(func.lower(AdminUser.email) == email))
        if user is None and email == settings.admin_web_email.casefold() and settings.admin_web_password:
            user = AdminUser(email=settings.admin_web_email.casefold(), name="Головний адміністратор", password_hash=hash_password(settings.admin_web_password), role="chief", active=True, email_verified_at=datetime.now(timezone.utc))
            session.add(user)
            await session.flush()
        if not user or not user.active or not verify_password(password, user.password_hash):
            await asyncio_sleep()
            return web.json_response({"ok": False, "error": "invalid_credentials"}, status=401)
        user.last_login_at = datetime.now(timezone.utc)
        await audit(session, user, request, "login")
        await session.commit()
        await session.refresh(user)
        token = create_admin_token(user)
    return web.json_response({"ok": True, "token": token, "user": {"email": user.email, "name": user.name, "role": user.role}})


async def asyncio_sleep() -> None:
    import asyncio
    await asyncio.sleep(0.35)


async def admin_me(request: web.Request) -> web.Response:
    user = await current_admin(request)
    return web.json_response({"ok": True, "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}})


async def dashboard(request: web.Request) -> web.Response:
    await current_admin(request)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    async with SessionLocal() as session:
        order_count = await session.scalar(select(func.count()).select_from(WebOrder)) or 0
        new_count = await session.scalar(select(func.count()).select_from(WebOrder).where(WebOrder.status == "new")) or 0
        revenue = await session.scalar(select(func.coalesce(func.sum(WebOrder.subtotal), 0)).where(WebOrder.status != "canceled")) or 0
        events = await session.scalar(select(func.count()).select_from(AnalyticsEvent).where(AnalyticsEvent.created_at >= since)) or 0
        popular = (await session.execute(select(AnalyticsEvent.data["id"].astext.label("product_id"), func.count().label("views")).where(AnalyticsEvent.event.in_(["product_view", "price_request_started", "add_to_cart"]), AnalyticsEvent.data.has_key("id")).group_by("product_id").order_by(desc("views")).limit(12))).all()
    return web.json_response({"orders": order_count, "new_orders": new_count, "revenue": float(revenue), "events_30d": events, "popular": [{"product_id": row.product_id, "views": row.views} for row in popular]})


async def list_orders(request: web.Request) -> web.Response:
    await current_admin(request)
    status = request.query.get("status")
    search = request.query.get("q", "").strip().casefold()[:120]
    attention = request.query.get("attention") == "1"
    try:
        limit = min(max(int(request.query.get("limit", "100")), 1), 250)
        offset = max(int(request.query.get("offset", "0")), 0)
    except ValueError:
        return web.json_response({"ok": False, "error": "invalid_pagination"}, status=422)
    async with SessionLocal() as session:
        query = select(WebOrder)
        if status in ORDER_STATUSES:
            query = query.where(WebOrder.status == status)
        if attention:
            query = query.where(WebOrder.status.in_(ATTENTION_STATUSES))
        if search:
            pattern = f"%{search}%"
            query = query.where(or_(
                func.lower(WebOrder.order_number).like(pattern),
                func.lower(func.coalesce(WebOrder.customer["name"].astext, "")).like(pattern),
                func.lower(func.coalesce(WebOrder.customer["phone"].astext, "")).like(pattern),
                func.lower(func.coalesce(WebOrder.telegram_username, "")).like(pattern),
                func.lower(func.coalesce(WebOrder.tracking_number, "")).like(pattern),
                func.lower(func.coalesce(WebOrder.supplier_order_number, "")).like(pattern),
                func.lower(cast(WebOrder.delivery, String)).like(pattern),
            ))
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = await session.scalar(count_query) or 0
        orders = (await session.scalars(query.order_by(WebOrder.created_at.desc()).offset(offset).limit(limit))).all()
    return web.json_response({"orders": [serialize_order(order) for order in orders], "total": total, "limit": limit, "offset": offset})


async def get_order(request: web.Request) -> web.Response:
    await current_admin(request)
    async with SessionLocal() as session:
        order = await session.get(WebOrder, int(request.match_info["order_id"]))
        if not order:
            raise web.HTTPNotFound()
    return web.json_response({"order": serialize_order(order)})


async def update_order(request: web.Request) -> web.Response:
    user = await current_admin(request)
    payload = await request.json()
    async with SessionLocal() as session:
        order = await session.get(WebOrder, int(request.match_info["order_id"]))
        if not order:
            raise web.HTTPNotFound()
        editable = {
            "manager_note": 4000,
            "tracking_number": 120,
            "telegram_username": 64,
            "drive_folder_url": 500,
            "supplier_order_number": 120,
            "problem_note": 4000,
        }
        before = {key: getattr(order, key) for key in ("status", *editable, "tracking_provider", "assigned_admin_id")}
        status = payload.get("status")
        if status is not None:
            if status not in ORDER_STATUSES:
                return web.json_response({"ok": False, "error": "invalid_status"}, status=422)
            order.status = status
        for field, max_length in editable.items():
            if field in payload:
                value = str(payload.get(field) or "").strip()[:max_length]
                if field == "telegram_username":
                    value = value.lstrip("@")
                if field == "drive_folder_url" and value and not value.startswith("https://"):
                    return web.json_response({"ok": False, "error": "invalid_drive_url"}, status=422)
                setattr(order, field, value or None)
        if "tracking_provider" in payload:
            provider = str(payload.get("tracking_provider") or "")
            if provider and provider not in TRACKING_PROVIDERS:
                return web.json_response({"ok": False, "error": "invalid_tracking_provider"}, status=422)
            order.tracking_provider = provider or None
        if "assigned_admin_id" in payload:
            assigned = payload.get("assigned_admin_id")
            order.assigned_admin_id = int(assigned) if assigned else None
        after = {key: getattr(order, key) for key in before}
        changes = {key: {"before": before[key], "after": after[key]} for key in before if before[key] != after[key]}
        if changes:
            history = list(order.status_history or [])
            history.append({
                "at": datetime.now(timezone.utc).isoformat(),
                "admin_id": user.id,
                "admin_email": user.email,
                "changes": changes,
            })
            order.status_history = history[-200:]
            await audit(session, user, request, "order_updated", "order", order.order_number, {"changes": changes})
        await session.commit()
        await session.refresh(order)
    return web.json_response({"ok": True, "order": serialize_order(order)})


async def list_prices(request: web.Request) -> web.Response:
    await current_admin(request)
    async with SessionLocal() as session:
        rows = (await session.scalars(select(PriceOverride).order_by(PriceOverride.product_id))).all()
    return web.json_response({"prices": [{"product_id": row.product_id, "price": float(row.price_uah), "enabled": row.enabled} for row in rows]})


async def save_price(request: web.Request) -> web.Response:
    user = await current_admin(request)
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
        old_price = float(row.price_uah) if row else None
        if row is None:
            row = PriceOverride(product_id=product_id, price_uah=price)
            session.add(row)
        else:
            row.price_uah = price
        row.enabled = bool(payload.get("enabled", True))
        await audit(session, user, request, "price_updated", "product", product_id, {"old_price": old_price, "new_price": float(price), "enabled": row.enabled})
        await session.commit()
    return web.json_response({"ok": True})


async def list_admins(request: web.Request) -> web.Response:
    await current_admin(request, chief_only=True)
    async with SessionLocal() as session:
        rows = (await session.scalars(select(AdminUser).order_by(AdminUser.created_at))).all()
    return web.json_response({"admins": [{"id": row.id, "email": row.email, "name": row.name, "role": row.role, "active": row.active, "created_at": row.created_at.isoformat(), "last_login_at": row.last_login_at.isoformat() if row.last_login_at else None} for row in rows]})


async def create_admin(request: web.Request) -> web.Response:
    chief = await current_admin(request, chief_only=True)
    payload = await request.json()
    email = str(payload.get("email", "")).strip().casefold()[:180]
    name, password = str(payload.get("name", "")).strip()[:120], str(payload.get("password", ""))
    if "@" not in email or not name or not _valid_password(password):
        return web.json_response({"ok": False, "error": "invalid_admin"}, status=422)
    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(AdminUser).where(AdminUser.active.is_(True))) or 0
        if count >= 4:
            return web.json_response({"ok": False, "error": "admin_limit"}, status=409)
        if await session.scalar(select(AdminUser).where(func.lower(AdminUser.email) == email)):
            return web.json_response({"ok": False, "error": "email_exists"}, status=409)
        user = AdminUser(email=email, name=name, password_hash=hash_password(password), role="manager", active=True, email_verified_at=datetime.now(timezone.utc))
        session.add(user)
        await session.flush()
        await audit(session, chief, request, "admin_created", "admin", str(user.id), {"email": email, "name": name})
        await session.commit()
    return web.json_response({"ok": True}, status=201)


async def update_admin(request: web.Request) -> web.Response:
    chief = await current_admin(request, chief_only=True)
    payload = await request.json()
    target_id = int(request.match_info["admin_id"])
    async with SessionLocal() as session:
        target = await session.get(AdminUser, target_id)
        if not target:
            raise web.HTTPNotFound()
        if target.role == "chief" or target.id == chief.id:
            return web.json_response({"ok": False, "error": "chief_protected"}, status=409)
        target.active = bool(payload.get("active", target.active))
        if payload.get("password"):
            if not _valid_password(str(payload["password"])):
                return web.json_response({"ok": False, "error": "weak_password"}, status=422)
            target.password_hash = hash_password(str(payload["password"]))
        await audit(session, chief, request, "admin_updated", "admin", str(target.id), {"email": target.email, "active": target.active, "password_reset": bool(payload.get("password"))})
        await session.commit()
    return web.json_response({"ok": True})


async def list_audit(request: web.Request) -> web.Response:
    await current_admin(request, chief_only=True)
    async with SessionLocal() as session:
        rows = (await session.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(500))).all()
    return web.json_response({"events": [{"id": row.id, "admin_email": row.admin_email, "action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "details": row.details, "ip_address": row.ip_address, "created_at": row.created_at.isoformat()} for row in rows]})


async def nova_poshta(request: web.Request) -> web.Response:
    settings = get_settings()
    if not settings.nova_poshta_api_key:
        return web.json_response({"ok": False, "error": "not_configured"}, status=503)
    kind, query, city_ref = request.match_info["kind"], request.query.get("q", "").strip()[:120], request.query.get("city_ref", "")[:64]
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
    app.router.add_get("/api/admin/captcha", admin_captcha)
    app.router.add_post("/api/admin/register", admin_register)
    app.router.add_post("/api/admin/verify-email", admin_verify_email)
    app.router.add_post("/api/admin/request-reset", admin_request_reset)
    app.router.add_post("/api/admin/reset-password", admin_reset_password)
    app.router.add_post("/api/admin/login", admin_login)
    app.router.add_get("/api/admin/me", admin_me)
    app.router.add_post("/api/admin/change-password", admin_change_password)
    app.router.add_get("/api/admin/dashboard", dashboard)
    app.router.add_get("/api/admin/orders", list_orders)
    app.router.add_get("/api/admin/orders/{order_id}", get_order)
    app.router.add_patch("/api/admin/orders/{order_id}", update_order)
    app.router.add_get("/api/admin/prices", list_prices)
    app.router.add_put("/api/admin/prices", save_price)
    app.router.add_get("/api/admin/users", list_admins)
    app.router.add_post("/api/admin/users", create_admin)
    app.router.add_patch("/api/admin/users/{admin_id}", update_admin)
    app.router.add_get("/api/admin/audit", list_audit)
    app.router.add_get("/api/nova-poshta/{kind}", nova_poshta)
