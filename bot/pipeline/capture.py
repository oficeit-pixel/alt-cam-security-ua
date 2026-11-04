"""Site -> CRM capture: every site lead and cart order becomes an inquiry with an owner card."""
from __future__ import annotations

import logging
from typing import Any

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import WebOrder
from bot.pipeline import links, notify, service

logger = logging.getLogger("altcam.pipeline")


def _lead_summary(payload: dict[str, Any]) -> str:
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    parts = [str(payload.get("type") or "Заявка з сайту")]
    for key in ("message", "comment"):
        value = payload.get(key) or client.get(key)
        if value:
            parts.append(str(value))
    if payload.get("page"):
        parts.append(f"Сторінка: {payload['page']}")
    return "\n".join(parts)[:3000]


async def capture_site_lead(bot, lead_id: int, payload: dict[str, Any]) -> str | None:
    """Returns the signed bot deep link for the client, or None if the pipeline is off/failed."""
    if not get_settings().pipeline_enabled:
        return None
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    try:
        async with SessionLocal() as session:
            inquiry = await service.create_inquiry(
                session, source="site_lead", summary=_lead_summary(payload), client_name=client.get("name"),
                phone=client.get("phone"), client_username=str(client.get("telegram") or "").lstrip("@") or None,
                site_lead_id=lead_id,
            )
            await session.commit()
            await notify.send_owner_card(bot, session, inquiry, header="🆕 <b>Нова заявка з сайту</b>")
            await session.commit()
        return links.bot_link("l", lead_id)
    except Exception as exc:
        logger.warning("pipeline_capture_lead_failed lead=%s (%s)", lead_id, type(exc).__name__)
        return None


async def capture_site_order(bot, order: WebOrder) -> str | None:
    if not get_settings().pipeline_enabled:
        return None
    customer = order.customer or {}
    delivery = order.delivery or {}
    summary = "\n".join(filter(None, [f"Замовлення з кошика {order.order_number}", str(delivery.get("comment") or "")]))
    try:
        async with SessionLocal() as session:
            inquiry = await service.create_inquiry(
                session, source="site_order", summary=summary, client_name=customer.get("name"), phone=customer.get("phone"),
                client_username=order.telegram_username, web_order_id=order.id,
            )
            await session.commit()
            await notify.send_owner_card(bot, session, inquiry, header="🛒 <b>Нове замовлення з сайту</b>")
            await session.commit()
        return links.bot_link("o", order.id)
    except Exception as exc:
        logger.warning("pipeline_capture_order_failed order=%s (%s)", order.order_number, type(exc).__name__)
        return None
