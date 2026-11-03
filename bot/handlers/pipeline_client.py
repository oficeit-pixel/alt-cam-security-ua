"""Client side of the order pipeline: capture every private message, instant auto-reply, FAQ buttons.

Router order matters: `deeplink_router` goes before `start.router`, `router` (catch-all) goes last.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import Inquiry, SiteLead, WebOrder
from bot.handlers.admin import is_admin
from bot.pipeline import links, notify, service, texts
from bot.pipeline.statuses import can_transition
from bot.states.states import CaptchaState, TermsState

logger = logging.getLogger("altcam.pipeline.client")
deeplink_router = Router(name="pipeline_deeplink")
router = Router(name="pipeline_client")
AUTO_REPLY_REPEAT = timedelta(hours=6)
CARD_REPEAT = timedelta(minutes=10)  # follow-up messages within 10 min: copy only, no new card
SITE_START_PREFIXES = ("site", "order", "buy", "consult")


def _message_summary(message: Message) -> str:
    text = message.text or message.caption or ""
    if message.photo:
        text = "[фото] " + text
    elif message.document:
        text = f"[файл {message.document.file_name or ''}] " + text
    elif message.contact:
        text = f"[контакт] {message.contact.phone_number}"
    elif message.location:
        text = "[геолокація]"
    return text.strip()[:3000] or "[повідомлення]"


async def _copy_to_owner(message: Message, session, inquiry: Inquiry, header: str | None, force_card: bool = False) -> None:
    settings = get_settings()
    owner = settings.owner_chat_id
    if not owner:
        return
    if header and (force_card or await service.card_is_stale(session, inquiry.id, owner, CARD_REPEAT)):
        await notify.send_owner_card(message.bot, session, inquiry, header=header, targets=[owner])
    try:
        copied = await message.bot.copy_message(owner, message.chat.id, message.message_id)
        await service.add_event(session, inquiry.id, "owner_copy", "system", None, owner_chat_id=owner,
                                owner_message_id=copied.message_id)
    except Exception as exc:
        logger.warning("owner_copy_failed inquiry=%s (%s)", inquiry.id, type(exc).__name__)


async def capture_client_message(message: Message) -> Inquiry:
    user = message.from_user
    now = service.utcnow()
    summary = _message_summary(message)
    async with SessionLocal() as session:
        inquiry = await service.find_open_for_client(session, user.id, now)
        is_new = inquiry is None
        new_wait = is_new or inquiry.awaiting_since is None
        if is_new:
            inquiry = await service.create_inquiry(
                session, source="bot", summary=summary, client_tg_id=user.id, client_chat_id=message.chat.id,
                client_username=user.username, client_name=user.full_name, now=now,
            )
        else:
            await service.record_client_message(session, inquiry, summary, now)
        if message.contact and not inquiry.phone:
            inquiry.phone = message.contact.phone_number[:32]
        need_auto_reply = is_new or (
            inquiry.auto_reply_at is not None and now - inquiry.auto_reply_at > AUTO_REPLY_REPEAT
            and (inquiry.last_owner_msg_at is None or inquiry.last_owner_msg_at < inquiry.auto_reply_at)
        )
        if need_auto_reply:
            inquiry.auto_reply_at = now
        await session.commit()
        if need_auto_reply:
            await message.answer(texts.auto_reply(inquiry.id, now), reply_markup=notify.client_faq_keyboard(),
                                 disable_web_page_preview=True)
        header = "🆕 <b>Новий запит у боті</b>" if is_new else f"💬 Нове повідомлення у запиті №{inquiry.id}"
        await _copy_to_owner(message, session, inquiry, header, force_card=new_wait)
        await session.commit()
    return inquiry


async def _start_site(message: Message) -> None:
    """Site button -> bot: greet immediately, capture as an inquiry (no captcha wall for sales)."""
    user = message.from_user
    now = service.utcnow()
    async with SessionLocal() as session:
        inquiry = await service.find_open_for_client(session, user.id, now)
        if inquiry is None:
            inquiry = await service.create_inquiry(
                session, source="bot", summary="Перейшов із сайту (кнопка Telegram)", client_tg_id=user.id,
                client_chat_id=message.chat.id, client_username=user.username, client_name=user.full_name, now=now,
            )
            inquiry.auto_reply_at = now
            inquiry.awaiting_since = None  # no escalation until the client actually writes
            await session.commit()
            is_new = True
        else:
            is_new = False
        await message.answer(texts.auto_reply(inquiry.id, now), reply_markup=notify.client_faq_keyboard(),
                             disable_web_page_preview=True)
        if is_new:
            await notify.send_owner_card(message.bot, session, inquiry, header="👋 Клієнт відкрив бота з сайту (ще не писав)",
                                         targets=[t for t in [get_settings().owner_chat_id] if t])
            await session.commit()


PIPELINE_START = r"^/start(@\w+)? ((site|order|buy|consult)[\w-]*|[ol]\d{1,12}_[A-Za-z0-9]{10})$"


@deeplink_router.message(CommandStart(deep_link=True), F.chat.type == "private", F.text.regexp(PIPELINE_START))
async def start_deeplink(message: Message, command: CommandObject) -> None:
    if not get_settings().pipeline_enabled:
        from aiogram.dispatcher.event.bases import SkipHandler
        raise SkipHandler()
    args = (command.args or "").strip()
    parsed = links.parse_start_param(args)
    if parsed is None:
        if args.startswith(SITE_START_PREFIXES):
            await _start_site(message)
        else:
            await message.answer("Посилання недійсне. Просто напишіть нам тут — менеджер відповість.",
                                 reply_markup=notify.client_faq_keyboard())
        return
    kind, object_id = parsed
    user = message.from_user
    async with SessionLocal() as session:
        if kind == "o":
            order = await session.get(WebOrder, object_id)
            inquiry = await service.inquiry_for_web_order(session, object_id) if order else None
            title = order.order_number if order else None
        else:
            lead = await session.get(SiteLead, object_id)
            inquiry = await service.inquiry_for_site_lead(session, object_id) if lead else None
            title = f"Заявка №{object_id}" if lead else None
        if inquiry is None or title is None:
            await message.answer("Посилання застаріло. Просто напишіть нам тут — менеджер відповість.",
                                 reply_markup=notify.client_faq_keyboard())
            return
        service.bind_client(inquiry, tg_id=user.id, chat_id=message.chat.id, username=user.username, full_name=user.full_name)
        await service.add_event(session, inquiry.id, "client_bound", "client", f"tg:{user.id}")
        await session.commit()
        await notify.send_owner_card(message.bot, session, inquiry, header="🔗 Клієнт підключив Telegram до запиту",
                                     targets=[t for t in [get_settings().owner_chat_id] if t])
        await session.commit()
    await message.answer(texts.site_order_bound_text(title), reply_markup=notify.client_faq_keyboard())


FAQ = {"pay": texts.faq_payment, "dlv": texts.faq_delivery, "war": texts.faq_warranty}


@router.callback_query(F.data.startswith("faq:"))
async def faq(callback: CallbackQuery) -> None:
    key = callback.data.split(":", 1)[1]
    if key in FAQ:
        await callback.message.answer(FAQ[key](), disable_web_page_preview=True)
        await callback.answer()
        return
    if key == "human":
        async with SessionLocal() as session:
            inquiry = await service.find_open_for_client(session, callback.from_user.id)
            if inquiry is None:
                inquiry = await service.create_inquiry(
                    session, source="bot", summary="Клієнт натиснув «Покликати менеджера»", client_tg_id=callback.from_user.id,
                    client_chat_id=callback.message.chat.id, client_username=callback.from_user.username,
                    client_name=callback.from_user.full_name,
                )
            else:
                await service.record_client_message(session, inquiry, "🙋 Покликати менеджера")
            await session.commit()
            await notify.send_owner_card(callback.bot, session, inquiry, header="🙋 <b>Клієнт кличе менеджера</b>", level=2)
            await session.commit()
        await callback.message.answer(texts.faq_human())
    await callback.answer()


@router.callback_query(F.data.startswith("cli:"))
async def client_decision(callback: CallbackQuery) -> None:
    _, raw_id, action = (callback.data.split(":") + ["", ""])[:3]
    if not raw_id.isdigit():
        await callback.answer()
        return
    async with SessionLocal() as session:
        inquiry = await session.get(Inquiry, int(raw_id))
        if inquiry is None or inquiry.client_tg_id != callback.from_user.id:
            await callback.answer("Запит не знайдено", show_alert=True)
            return
        if action == "ok":
            if can_transition(inquiry.status, "confirmed"):
                await service.transition(session, inquiry, "confirmed", actor="client")
            await service.record_client_message(session, inquiry, "✅ Клієнт підтвердив замовлення")
            header, reply = "✅ <b>Клієнт підтвердив замовлення</b>", "Дякуємо! Замовлення підтверджено ✅ Менеджер надішле реквізити/деталі оплати."
        elif action == "no":
            if can_transition(inquiry.status, "rejected"):
                await service.transition(session, inquiry, "rejected", actor="client", note="Клієнт: неактуально")
            header, reply = "❌ Клієнт відмовився (неактуально)", "Зрозуміло, дякуємо за відповідь! Якщо знадобиться — пишіть сюди."
        else:
            await service.record_client_message(session, inquiry, "❓ У клієнта є питання")
            header, reply = "❓ <b>У клієнта є питання</b>", "Напишіть, будь ласка, ваше питання — менеджер відповість."
        await session.commit()
        await notify.send_owner_card(callback.bot, session, inquiry, header=header,
                                     targets=[t for t in [get_settings().owner_chat_id] if t])
        await session.commit()
    await callback.message.answer(reply)
    await callback.answer()


@router.message(F.chat.type == "private",
                StateFilter(None, CaptchaState.waiting_for_captcha, TermsState.waiting_for_accept),
                ~F.text.startswith("/"))
async def capture(message: Message) -> None:
    settings = get_settings()
    if not settings.pipeline_enabled or message.from_user is None or is_admin(message.from_user.id):
        return
    await capture_client_message(message)
