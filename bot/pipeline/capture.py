"""Site -> CRM capture: every site lead and cart order becomes an inquiry with an owner card."""
from __future__ import annotations

import logging
from typing import Any

from bot.config import get_settings
from bot.db.base import SessionLocal
from sqlalchemy import select

from bot.db.models import Inquiry, InquiryEvent, WebOrder
from bot.pipeline.statuses import TERMINAL
from bot.pipeline.delivery import send_client_text
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


async def capture_site_order(bot, order: WebOrder, *, context=None) -> str | None:
    if not get_settings().pipeline_enabled:
        return None
    customer = order.customer or {}
    delivery = order.delivery or {}
    summary = "\n".join(filter(None, [f"Замовлення з кошика {order.order_number}", str(delivery.get("comment") or "")]))
    try:
        async with SessionLocal() as session:
            # Serialize retries of the very same web order. Separate orders must never overwrite one another.
            await session.scalar(select(WebOrder.id).where(WebOrder.id == order.id).with_for_update())
            if await service.inquiry_for_web_order(session, order.id):
                return links.bot_link("o", order.id)
            inquiry = None
            if context:
                inquiry_id, user_id = context
                inquiry = await session.scalar(select(Inquiry).where(
                    Inquiry.id == inquiry_id, Inquiry.client_chat_id == user_id, Inquiry.client_tg_id == user_id,
                    Inquiry.business_connection_id.is_(None), Inquiry.status.not_in(TERMINAL),
                    Inquiry.web_order_id.is_(None),
                ).with_for_update())
            linked = inquiry is not None
            if linked:
                inquiry.web_order_id = order.id
                inquiry.phone = customer.get("phone") or inquiry.phone
                await service.add_event(session, inquiry.id, "checkout_linked", "client", order.order_number)
            else:
                inquiry = await service.create_inquiry(
                    session, source="site_order", summary=summary, client_name=customer.get("name"), phone=customer.get("phone"),
                    client_username=order.telegram_username, web_order_id=order.id,
                )
            await session.commit()
            header = "🛒 <b>Замовлення оформлено</b>"
            if linked and bot:
                await send_client_text(bot, inquiry, f"Замовлення {order.order_number} прийнято ✅ Запит №{inquiry.id}.")
                for chat_id in notify.escalation_targets(1):
                    previous = await session.scalar(select(InquiryEvent.owner_message_id).where(
                        InquiryEvent.inquiry_id == inquiry.id, InquiryEvent.kind == "owner_notified",
                        InquiryEvent.owner_chat_id == chat_id, InquiryEvent.owner_message_id.is_not(None),
                    ).order_by(InquiryEvent.id.desc()).limit(1))
                    if previous:
                        try:
                            await bot.edit_message_text(text=notify.owner_card(inquiry, order, header),
                                chat_id=chat_id, message_id=previous, reply_markup=notify.owner_keyboard(inquiry, order))
                            continue
                        except Exception as exc:
                            logger.warning("checkout_card_edit_failed inquiry=%s (%s)", inquiry.id, type(exc).__name__)
                    await notify.send_owner_card(bot, session, inquiry, header=header, targets=[chat_id])
            else:
                await notify.send_owner_card(bot, session, inquiry, header=header)
            await session.commit()
        return links.bot_link("o", order.id)
    except Exception as exc:
        logger.warning("pipeline_capture_order_failed order=%s (%s)", order.order_number, type(exc).__name__)
        return None
