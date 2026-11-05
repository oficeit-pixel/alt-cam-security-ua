"""Inquiry persistence: capture, state transitions, SLA queries. No Telegram calls here."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Inquiry, InquiryEvent, WebOrder
from bot.pipeline.statuses import TERMINAL, WEB_ORDER_STATUS, can_transition

OPEN_WINDOW_DAYS = 14
# Explicit manager acknowledgement ends the previous response SLA, not future questions.
SLA_ACK_STATUSES = frozenset({"taken", "offer_sent", "paid", "supplier_ordered", "supplier_paid", "shipped"})


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _history(inquiry: Inquiry, entry: dict[str, Any]) -> None:
    history = list(inquiry.status_history or [])
    history.append(entry)
    inquiry.status_history = history[-200:]


async def add_event(session: AsyncSession, inquiry_id: int, kind: str, actor: str, text: str | None = None,
                    owner_chat_id: int | None = None, owner_message_id: int | None = None) -> InquiryEvent:
    event = InquiryEvent(inquiry_id=inquiry_id, kind=kind, actor=actor, text=(text or "")[:4000] or None,
                         owner_chat_id=owner_chat_id, owner_message_id=owner_message_id)
    session.add(event)
    await session.flush()
    return event


async def create_inquiry(session: AsyncSession, *, source: str, summary: str = "", client_tg_id: int | None = None,
                         client_chat_id: int | None = None, client_username: str | None = None,
                         client_name: str | None = None, phone: str | None = None, site_lead_id: int | None = None,
                         web_order_id: int | None = None, now: datetime | None = None,
                         business_connection_id: str | None = None) -> Inquiry:
    now = now or utcnow()
    inquiry = Inquiry(
        source=source, status="new", summary=(summary or "")[:4000], client_tg_id=client_tg_id,
        client_chat_id=client_chat_id, client_username=(client_username or "")[:64] or None,
        client_name=(client_name or "")[:255] or None, phone=(phone or "")[:32] or None,
        site_lead_id=site_lead_id, web_order_id=web_order_id, awaiting_since=now,
        business_connection_id=business_connection_id,
        last_client_msg_at=now, reminder_level=0, status_history=[{"at": now.isoformat(), "status": "new", "actor": source}],
    )
    session.add(inquiry)
    await session.flush()
    await add_event(session, inquiry.id, "created", "client", summary)
    return inquiry


async def find_open_for_client(session: AsyncSession, client_tg_id: int, now: datetime | None = None) -> Inquiry | None:
    cutoff = (now or utcnow()) - timedelta(days=OPEN_WINDOW_DAYS)
    return await session.scalar(
        select(Inquiry)
        .where(Inquiry.client_tg_id == client_tg_id, Inquiry.status.not_in(TERMINAL), Inquiry.created_at >= cutoff)
        .order_by(Inquiry.created_at.desc())
        .limit(1)
    )


async def record_client_message(session: AsyncSession, inquiry: Inquiry, text: str, now: datetime | None = None) -> None:
    now = now or utcnow()
    inquiry.last_client_msg_at = now
    if inquiry.awaiting_since is None:
        inquiry.awaiting_since = now
        inquiry.reminder_level = 0
    await add_event(session, inquiry.id, "client_message", "client", text)


async def record_owner_reply(session: AsyncSession, inquiry: Inquiry, text: str, owner_id: int | None,
                             now: datetime | None = None, kind: str = "owner_reply") -> None:
    now = now or utcnow()
    inquiry.last_owner_msg_at = now
    inquiry.first_response_at = inquiry.first_response_at or now
    inquiry.awaiting_since = None
    inquiry.reminder_level = 0
    await add_event(session, inquiry.id, kind, "owner", text)


async def transition(session: AsyncSession, inquiry: Inquiry, target: str, *, actor: str, owner_id: int | None = None,
                     note: str | None = None, now: datetime | None = None) -> str:
    now = now or utcnow()
    before = inquiry.status
    if not can_transition(before, target):
        raise ValueError(f"invalid_transition:{before}->{target}")
    inquiry.status = target
    if target == "taken" and inquiry.taken_at is None:
        inquiry.taken_at, inquiry.taken_by = now, owner_id
    if actor == "owner" and target in SLA_ACK_STATUSES:
        inquiry.awaiting_since = None
        inquiry.reminder_level = 0
    if target in TERMINAL:
        inquiry.awaiting_since = None
        inquiry.reminder_level = 0
        if note:
            inquiry.closed_reason = note[:2000]
    _history(inquiry, {"at": now.isoformat(), "status": target, "before": before, "actor": actor, **({"note": note} if note else {})})
    await add_event(session, inquiry.id, "status", actor, f"{before}->{target}" + (f": {note}" if note else ""))
    web_status = WEB_ORDER_STATUS.get(target)
    if web_status and inquiry.web_order_id:
        order = await session.get(WebOrder, inquiry.web_order_id)
        if order and order.status not in {"completed", "canceled"}:
            history = list(order.status_history or [])
            history.append({"at": now.isoformat(), "admin_email": "pipeline-bot", "changes": {"status": {"before": order.status, "after": web_status}}})
            order.status_history = history[-200:]
            order.status = web_status
            if target == "shipped" and inquiry.ttn:
                order.tracking_number, order.tracking_provider = inquiry.ttn, "nova_poshta"
    return before


async def inquiry_by_owner_message(session: AsyncSession, chat_id: int, message_id: int) -> Inquiry | None:
    inquiry_id = await session.scalar(
        select(InquiryEvent.inquiry_id)
        .where(InquiryEvent.owner_chat_id == chat_id, InquiryEvent.owner_message_id == message_id)
        .order_by(InquiryEvent.id.desc()).limit(1)
    )
    return await session.get(Inquiry, inquiry_id) if inquiry_id else None


async def card_is_stale(session: AsyncSession, inquiry_id: int, chat_id: int, max_age: timedelta,
                        now: datetime | None = None) -> bool:
    last = await session.scalar(
        select(InquiryEvent.created_at)
        .where(InquiryEvent.inquiry_id == inquiry_id, InquiryEvent.kind == "owner_notified", InquiryEvent.owner_chat_id == chat_id)
        .order_by(InquiryEvent.id.desc()).limit(1)
    )
    return last is None or (now or utcnow()) - last > max_age


def stale_sla_acknowledgement(inquiry: Inquiry) -> datetime | None:
    """Repair only a proven old wait. Never suppress a question sent after the action."""
    if inquiry.awaiting_since is None or inquiry.status not in SLA_ACK_STATUSES:
        return None
    for entry in reversed(inquiry.status_history or []):
        if not isinstance(entry, dict) or entry.get("status") != inquiry.status:
            continue
        if entry.get("actor") != "owner":
            return None
        try:
            at = datetime.fromisoformat(entry["at"])
            if at.tzinfo is None:
                return None
            if inquiry.awaiting_since <= at and (inquiry.last_client_msg_at is None or inquiry.last_client_msg_at <= at):
                return at
        except (KeyError, TypeError, ValueError):
            pass
        return None
    return None


async def repair_stale_sla(session: AsyncSession) -> int:
    rows = (await session.scalars(select(Inquiry).where(
        Inquiry.awaiting_since.is_not(None), Inquiry.status.in_(SLA_ACK_STATUSES),
    ))).all()
    repaired = 0
    for inquiry in rows:
        at = stale_sla_acknowledgement(inquiry)
        if at is None:
            continue
        # Compare-and-set: a concurrent client message/status update must win.
        changed = await session.scalar(update(Inquiry).where(
            Inquiry.id == inquiry.id, Inquiry.status == inquiry.status,
            Inquiry.awaiting_since == inquiry.awaiting_since,
            or_(Inquiry.last_client_msg_at.is_(None), Inquiry.last_client_msg_at <= at),
        ).values(awaiting_since=None, reminder_level=0).returning(Inquiry.id))
        if changed is not None:
            await add_event(session, inquiry.id, "sla_repaired", "system", "Previous wait acknowledged by manager status")
            repaired += 1
    return repaired


def reminder_level_for(waiting_minutes: float, thresholds: list[int]) -> int:
    return sum(1 for limit in thresholds if waiting_minutes >= limit)


async def due_reminders(session: AsyncSession, thresholds: list[int], now: datetime | None = None) -> list[tuple[Inquiry, int]]:
    now = now or utcnow()
    first = min(thresholds)
    rows = (await session.scalars(
        select(Inquiry).where(
            Inquiry.awaiting_since.is_not(None),
            Inquiry.awaiting_since <= now - timedelta(minutes=first),
            Inquiry.status.not_in(TERMINAL),
            Inquiry.reminder_level < len(thresholds),
        ).order_by(Inquiry.awaiting_since).limit(200)
    )).all()
    result = []
    for inquiry in rows:
        level = reminder_level_for((now - inquiry.awaiting_since).total_seconds() / 60, thresholds)
        if level > inquiry.reminder_level:
            result.append((inquiry, level))
    return result


async def claim_reminder(session: AsyncSession, inquiry_id: int, level: int) -> bool:
    """Atomic guard so two app instances never send the same reminder twice."""
    claimed = await session.scalar(
        update(Inquiry).where(Inquiry.id == inquiry_id, Inquiry.reminder_level < level, Inquiry.awaiting_since.is_not(None))
        .values(reminder_level=level).returning(Inquiry.id)
    )
    return claimed is not None


async def due_followups(session: AsyncSession, hours: int, now: datetime | None = None) -> list[Inquiry]:
    """Offer/stock sent, client silent for `hours` after our last message, no follow-up yet."""
    now = now or utcnow()
    return list((await session.scalars(
        select(Inquiry).where(
            Inquiry.status.in_(("stock_checked", "offer_sent")),
            Inquiry.followup_sent_at.is_(None),
            Inquiry.awaiting_since.is_(None),
            Inquiry.last_owner_msg_at.is_not(None),
            Inquiry.last_owner_msg_at <= now - timedelta(hours=hours),
            or_(Inquiry.last_client_msg_at.is_(None), Inquiry.last_client_msg_at <= Inquiry.last_owner_msg_at),
        ).limit(100)
    )).all())


async def claim_followup(session: AsyncSession, inquiry_id: int, now: datetime | None = None) -> bool:
    claimed = await session.scalar(
        update(Inquiry).where(Inquiry.id == inquiry_id, Inquiry.followup_sent_at.is_(None))
        .values(followup_sent_at=now or utcnow()).returning(Inquiry.id)
    )
    return claimed is not None


async def open_inquiries(session: AsyncSession, limit: int = 50) -> list[Inquiry]:
    return list((await session.scalars(
        select(Inquiry).where(Inquiry.status.not_in(TERMINAL))
        .order_by(Inquiry.awaiting_since.is_(None), Inquiry.awaiting_since, Inquiry.created_at).limit(limit)
    )).all())


async def shipped_with_ttn(session: AsyncSession) -> list[Inquiry]:
    return list((await session.scalars(
        select(Inquiry).where(Inquiry.status == "shipped", Inquiry.ttn.is_not(None)).limit(100)
    )).all())


def sla_summary(inquiries: list[Inquiry], now: datetime | None = None) -> dict[str, Any]:
    now = now or utcnow()
    waiting = [i for i in inquiries if i.awaiting_since is not None]
    minutes = [(now - i.awaiting_since).total_seconds() / 60 for i in waiting]
    return {
        "open": len(inquiries),
        "waiting": len(waiting),
        "waiting_over_15m": sum(1 for m in minutes if m >= 15),
        "waiting_over_1h": sum(1 for m in minutes if m >= 60),
        "oldest_wait_minutes": int(max(minutes)) if minutes else 0,
        "new_not_taken": sum(1 for i in inquiries if i.status == "new"),
    }


def serialize(inquiry: Inquiry, now: datetime | None = None) -> dict[str, Any]:
    now = now or utcnow()
    return {
        "id": inquiry.id, "source": inquiry.source, "status": inquiry.status,
        "client_name": inquiry.client_name, "client_username": inquiry.client_username, "phone": inquiry.phone,
        "summary": inquiry.summary, "web_order_id": inquiry.web_order_id, "site_lead_id": inquiry.site_lead_id,
        "payment_method": inquiry.payment_method, "ttn": inquiry.ttn,
        "waiting_minutes": int((now - inquiry.awaiting_since).total_seconds() // 60) if inquiry.awaiting_since else None,
        "reminder_level": inquiry.reminder_level,
        "first_response_at": inquiry.first_response_at.isoformat() if inquiry.first_response_at else None,
        "created_at": inquiry.created_at.isoformat() if inquiry.created_at else None,
        "status_history": inquiry.status_history or [],
    }


async def inquiry_for_web_order(session: AsyncSession, web_order_id: int) -> Inquiry | None:
    return await session.scalar(select(Inquiry).where(Inquiry.web_order_id == web_order_id).order_by(Inquiry.id.desc()).limit(1))


async def inquiry_for_site_lead(session: AsyncSession, site_lead_id: int) -> Inquiry | None:
    return await session.scalar(select(Inquiry).where(Inquiry.site_lead_id == site_lead_id).order_by(Inquiry.id.desc()).limit(1))


def bind_client(inquiry: Inquiry, *, tg_id: int, chat_id: int, username: str | None, full_name: str | None) -> None:
    if inquiry.client_tg_id is not None and inquiry.client_tg_id != tg_id:
        raise ValueError("inquiry_already_bound")
    inquiry.client_tg_id, inquiry.client_chat_id = tg_id, chat_id
    inquiry.business_connection_id = None  # the client is in the bot chat now: answer there
    inquiry.client_username = (username or "")[:64] or inquiry.client_username
    inquiry.client_name = inquiry.client_name or (full_name or "")[:255] or None
