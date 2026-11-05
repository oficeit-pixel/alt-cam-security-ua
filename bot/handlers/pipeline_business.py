"""Telegram Business: the bot connected to the owner's personal account (@OficeITHelp).

Clients keep talking to a person; the bot only watches the chat:
* incoming message from a client  -> inquiry (source=telegram_business) + owner card + reminders 5/15/60;
* optional single acknowledgement in the owner's name (BUSINESS_AUTOREPLY_ENABLED, BUSINESS_AUTOREPLY_TEXT);
* outgoing message written by the owner himself -> inquiry marked answered / taken (reminders stop).

Only connections of the owner are accepted (OWNER_USERNAMES / ADMIN_CHAT_ID / ADMIN_IDS): anybody can connect
a public bot to their own account, such connections are stored with allowed=false and ignored.
Requires `business_connection` and `business_message` in allowed_updates (main.py resolves them automatically).
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import BusinessConnection, Message

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import BusinessConnectionRecord
from bot.handlers.admin import is_admin
from bot.pipeline import contacts, notify, service, texts
from bot.pipeline.statuses import can_transition

logger = logging.getLogger("altcam.pipeline.business")
router = Router(name="pipeline_business")
SOURCE = "telegram_business"


def connection_can_reply(connection: BusinessConnection) -> bool:
    """Bot API 9.0 moved `can_reply` into `rights` (BusinessBotRights); support both shapes."""
    rights = getattr(connection, "rights", None)
    if rights is not None:
        return bool(getattr(rights, "can_reply", False))
    return bool(getattr(connection, "can_reply", False))


def connection_allowed(user_id: int, username: str | None) -> bool:
    settings = get_settings()
    return is_admin(user_id) or settings.contact_role_for_username(username) == "owner"


async def _store_connection(session, connection: BusinessConnection) -> BusinessConnectionRecord:
    user = connection.user
    allowed = connection_allowed(user.id, user.username)
    record = await session.get(BusinessConnectionRecord, connection.id)
    if record is None:
        record = BusinessConnectionRecord(id=connection.id, user_id=user.id, user_chat_id=connection.user_chat_id)
        session.add(record)
    record.user_id, record.user_chat_id = user.id, connection.user_chat_id
    record.username = (user.username or "")[:64] or None
    record.can_reply = connection_can_reply(connection)
    record.is_enabled = bool(connection.is_enabled)
    record.allowed = allowed
    await session.flush()
    return record


@router.business_connection()
async def on_business_connection(connection: BusinessConnection) -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        record = await _store_connection(session, connection)
        registered = None
        if record.allowed and settings.contact_role_for_username(record.username) == "owner":
            registered = await contacts.register(session, "owner", record.user_chat_id, record.username)
        await session.commit()
    logger.info("business_connection id=%s user=%s enabled=%s can_reply=%s allowed=%s",
                connection.id, connection.user.id, connection.is_enabled, record.can_reply, record.allowed)
    if not record.allowed:
        return
    if connection.is_enabled:
        lines = ["✅ Бот підключено до вашого акаунта (Telegram Business).",
                 "Нові повідомлення клієнтів в особистих чатах потраплять у CRM з нагадуваннями 5/15/60 хв."]
        if not record.can_reply:
            lines.append("⚠️ Немає дозволу «відповідати на повідомлення» — автопідтвердження клієнту вимкнене.")
        if registered == "registered":
            lines.append("Вас зареєстровано як власника для сповіщень.")
    else:
        lines = ["⏸ Бізнес-підключення вимкнене: особисті чати більше не відстежуються."]
    try:
        await connection.bot.send_message(record.user_chat_id, "\n".join(lines))
    except Exception as exc:  # owner never started the bot
        logger.warning("business_connection_notify_failed (%s)", type(exc).__name__)


async def _connection(session, bot, connection_id: str) -> BusinessConnectionRecord | None:
    record = await session.get(BusinessConnectionRecord, connection_id)
    if record is None and bot is not None:
        try:  # update missed (e.g. bot was offline when connected)
            record = await _store_connection(session, await bot.get_business_connection(connection_id))
        except Exception as exc:
            logger.warning("business_connection_lookup_failed (%s)", type(exc).__name__)
            return None
    return record


def _summary(message: Message) -> str:
    from bot.handlers.pipeline_client import _message_summary

    return _message_summary(message)


async def handle_business_message(message: Message, now=None) -> str:
    """Returns what happened: ignored | owner_reply | captured_new | captured | skipped."""
    settings = get_settings()
    if not (settings.pipeline_enabled and settings.business_enabled) or not message.business_connection_id:
        return "ignored"
    if message.sender_business_bot is not None or message.chat.type != "private" or message.from_user is None:
        return "ignored"  # sent by a bot (incl. our own acknowledgement) or not a 1:1 chat
    now = now or service.utcnow()
    async with SessionLocal() as session:
        record = await _connection(session, message.bot, message.business_connection_id)
        if record is None or not record.allowed or not record.is_enabled:
            await session.commit()
            return "ignored"
        client_id = message.chat.id
        if client_id in settings.business_ignored_ids or is_admin(client_id) or client_id == record.user_id:
            return "skipped"
        if message.from_user.id == record.user_id:
            inquiry = await service.find_open_for_client(session, client_id, now)
            if inquiry is None:
                return "skipped"  # owner writes first / private conversation: nothing to track
            await service.record_owner_reply(session, inquiry, _summary(message), record.user_id, now, kind="owner_business_reply")
            if inquiry.status == "new" and can_transition("new", "taken"):
                await service.transition(session, inquiry, "taken", actor="owner", owner_id=record.user_id, now=now)
            inquiry.business_connection_id = message.business_connection_id
            if settings.ai_active and settings.ai_pause_on_owner_reply:
                from bot.ai import runtime as ai_runtime

                await ai_runtime.set_paused(session, client_id, True, "owner_reply")  # owner took over this chat
            await session.commit()
            return "owner_reply"
        user = message.from_user
        inquiry = await service.find_open_for_client(session, client_id, now)
        is_new = inquiry is None
        new_wait = is_new or inquiry.awaiting_since is None
        summary = _summary(message)
        if is_new:
            inquiry = await service.create_inquiry(
                session, source=SOURCE, summary=summary, client_tg_id=user.id, client_chat_id=client_id,
                client_username=user.username, client_name=user.full_name, now=now,
                business_connection_id=message.business_connection_id,
            )
        else:
            await service.record_client_message(session, inquiry, summary, now)
            inquiry.business_connection_id = message.business_connection_id
        if message.contact and not inquiry.phone:
            inquiry.phone = message.contact.phone_number[:32]
        await session.commit()
        ai_state = "disabled"
        if settings.ai_active and record.can_reply:
            from bot.ai import runtime as ai_runtime

            ai_state = await ai_runtime.respond(message.bot, session, inquiry, business=True, now=now)
        send_ack = is_new and settings.business_autoreply_enabled and record.can_reply and ai_state not in {"replied", "handoff"}
        if send_ack:
            inquiry.auto_reply_at = now
            await session.commit()
            try:
                await message.bot.send_message(client_id, texts.business_ack(now),
                                               business_connection_id=message.business_connection_id)
                await service.add_event(session, inquiry.id, "business_ack", "system", texts.business_ack(now))
            except Exception as exc:
                logger.warning("business_ack_failed inquiry=%s (%s)", inquiry.id, type(exc).__name__)
        if ai_state != "handoff" and (is_new or (new_wait and ai_state != "replied")):
            header = ("🆕 <b>Новий запит в особистому Telegram</b>" if is_new
                      else f"💬 Клієнт знову пише в особистому Telegram (запит №{inquiry.id})")
            if ai_state == "replied":
                header += " · 🤖 AI відповів"
            await notify.send_owner_card(message.bot, session, inquiry, header=header,
                                         targets=[t for t in [settings.owner_chat_id] if t])
        await session.commit()
    return "captured_new" if is_new else "captured"


@router.business_message()
async def on_business_message(message: Message) -> None:
    await handle_business_message(message)
