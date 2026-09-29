"""Durable website lead inbox. No real contacts or payloads are logged."""
import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from bot.db.base import SessionLocal
from bot.db.models import SiteLead


def normalize_lead(payload):
    if not isinstance(payload, dict):
        raise ValueError("invalid_payload")
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > 16384:
        raise ValueError("payload_too_large")
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    def field(key, limit):
        value = client.get(key, payload.get(key, ""))
        if value is None:
            value = ""
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError("invalid_" + key)
        return value.strip()
    name, phone, email, telegram = field("name", 255), field("phone", 32), field("email", 255), field("telegram", 64)
    phone = re.sub(r"[\s()\-]", "", phone)
    if re.fullmatch(r"0\d{9}", phone):
        phone = "+38" + phone
    elif re.fullmatch(r"380\d{9}", phone):
        phone = "+" + phone
    if not (re.fullmatch(r"\+380\d{9}", phone) or re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or re.fullmatch(r"@?[A-Za-z][A-Za-z0-9_]{4,31}", telegram)):
        raise ValueError("invalid_contact")
    message = payload.get("message") or "\n".join(
        f"{key}: {payload[key]}" for key in ("object", "cameras", "nightVision", "phoneView", "technicalNote") if payload.get(key) is not None
    )
    result = dict(payload)
    for key, value, limit in (("message", message, 4000), ("type", payload.get("type", "Заявка"), 100), ("page", payload.get("page", ""), 1000)):
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError("invalid_" + key)
        result[key] = value
    result["client"] = {**client, "name": name, "phone": phone, "email": email, "telegram": telegram}
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 16384:
        raise ValueError("payload_too_large")
    return result


async def save_lead(payload, remote):
    salt = os.environ.get("LEAD_IP_HASH_SALT", "")
    # No unsalted hash fallback: omit IP metadata until configured.
    ip_hash = hashlib.sha256((salt + ":" + remote).encode()).hexdigest() if salt and remote else None
    client = payload["client"]
    lead = SiteLead(type=payload["type"], name=client["name"], phone=client["phone"], email=client["email"], message=payload["message"], payload=payload, page=payload["page"], ip_hash=ip_hash)
    async with SessionLocal() as session:
        session.add(lead)
        await session.commit()
        return lead.id


async def deliver_lead(lead_id, bot, targets, render):
    if not bot or not targets:
        return
    for target in dict.fromkeys(targets):
        async with SessionLocal() as session:
            lead = await session.scalar(select(SiteLead).where(SiteLead.id == lead_id).with_for_update(skip_locked=True))
            if lead is None or lead.telegram_sent:
                return
            delivered = list(lead.telegram_delivered or [])
            if str(target) not in delivered:
                try:
                    # Plain text avoids invalid HTML when a large message is shortened.
                    await asyncio.wait_for(bot.send_message(target, render(lead.payload), parse_mode=None), timeout=10)
                    delivered.append(str(target))
                    lead.telegram_delivered = delivered
                    lead.telegram_error = None
                except Exception as exc:
                    lead.telegram_error = type(exc).__name__
            lead.telegram_sent = all(str(t) in delivered for t in targets)
            await session.commit()


async def pending_lead_ids():
    async with SessionLocal() as session:
        return list(await session.scalars(select(SiteLead.id).where(SiteLead.telegram_sent.is_(False), SiteLead.created_at >= datetime.now(timezone.utc) - timedelta(hours=48)).order_by(SiteLead.id).limit(100)))
