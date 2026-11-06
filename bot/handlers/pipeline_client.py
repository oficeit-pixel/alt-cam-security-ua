"""Client side of the order pipeline: capture every private message, instant auto-reply, FAQ buttons.

Router order matters: `deeplink_router` goes before `start.router`, `router` (catch-all) goes last.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
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


async def safe_ack(message: Message, text: str) -> bool:
    """A failed acknowledgement must not prevent owner notification."""
    try:
        await message.answer(text, reply_markup=notify.client_faq_keyboard(), disable_web_page_preview=True)
        return True
    except TelegramAPIError as exc:
        logger.warning("client_ack_failed (%s)", type(exc).__name__)
        return False


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
    for owner in notify.escalation_targets(1):
        if header and (force_card or await service.card_is_stale(session, inquiry.id, owner, CARD_REPEAT)):
            await notify.send_owner_card(message.bot, session, inquiry, header=header, targets=[owner])
        try:
            copied = await message.bot.copy_message(owner, message.chat.id, message.message_id)
            await service.add_event(session, inquiry.id, "owner_copy", "system", None, owner_chat_id=owner,
                                    owner_message_id=copied.message_id)
        except Exception as exc:
            logger.warning("owner_copy_failed inquiry=%s (%s)", inquiry.id, type(exc).__name__)


async def capture_client_message(message: Message) -> Inquiry:
    settings = get_settings()
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
            inquiry.business_connection_id = None  # latest message came to the bot: answer in the bot chat
        if message.contact and not inquiry.phone:
            inquiry.phone = message.contact.phone_number[:32]
        need_auto_reply = is_new or inquiry.auto_reply_at is None or (
            inquiry.auto_reply_at is not None and now - inquiry.auto_reply_at > AUTO_REPLY_REPEAT
            and (inquiry.last_owner_msg_at is None or inquiry.last_owner_msg_at < inquiry.auto_reply_at)
        )
        await session.commit()
        ai_state = "disabled"
        if settings.ai_active:
            from bot.ai import runtime as ai_runtime

            ai_state = await ai_runtime.respond(message.bot, session, inquiry, now=now)
        if ai_state in {"replied", "handoff"}:
            if need_auto_reply:
                inquiry.auto_reply_at = now  # the consultant already answered: it counts as the acknowledgement
        elif need_auto_reply:
            if await safe_ack(message, texts.auto_reply(inquiry.id, now)):
                inquiry.auto_reply_at = now
        elif ai_state == "failed":  # AI down mid-conversation: never leave the client without an answer
            from bot.ai import runtime as ai_runtime

            try:
                await message.answer(ai_runtime.handoff_client_text(
                    now, ai_runtime.detect_language(message.text or message.caption or "")))
            except TelegramAPIError as exc:
                logger.warning("client_ack_failed (%s)", type(exc).__name__)
        header = "🆕 <b>Новий запит у боті</b>" if is_new else f"💬 Нове повідомлення у запиті №{inquiry.id}"
        if ai_state == "replied":
            header += " · 🤖 AI відповів"
        await _copy_to_owner(message, session, inquiry, None if ai_state == "handoff" else header,
                             force_card=ai_state != "handoff" and (is_new or (new_wait and ai_state != "replied")))
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
            inquiry.awaiting_since = None  # no escalation until the client actually writes
            await session.commit()
            is_new = True
        else:
            is_new = False
        greeting = (f"Запит №{inquiry.id}. Вітаю в ALT-CAM! Я автоматизований помічник. "
                    "Що вам потрібно: підібрати товар чи замовити послугу? "
                    "Для монтажу вкажіть місто й тип об’єкта. Щоб підключити людину, напишіть «Хочу менеджера».")
        if get_settings().capture_before_terms:
            from html import escape
            greeting += f'\n\nНадсилаючи повідомлення, ви погоджуєтесь з <a href="{escape(get_settings().privacy_url)}">Політикою ПД</a>.'
        from bot.ai import runtime as ai_runtime
        if not get_settings().ai_active or await ai_runtime.is_paused(session, user.id):
            greeting = texts.auto_reply(inquiry.id, now)
        if await safe_ack(message, greeting):
            inquiry.auto_reply_at = now
        await session.commit()
        if is_new:
            await notify.send_owner_card(message.bot, session, inquiry, header="👋 Клієнт відкрив бота з сайту (ще не писав)",
                                         targets=notify.escalation_targets(1))
            await session.commit()


ROLE_LABELS = {"owner": "власник (основні сповіщення)", "second": "другий контакт (нагадування з 2-го рівня)"}


def _contact_role(message: Message) -> str | None:
    user = message.from_user
    return get_settings().contact_role_for_username(user.username) if user else None


@deeplink_router.message(CommandStart(), F.chat.type == "private", F.text.regexp(r"^/start(@\w+)?$"),
                         lambda message: _contact_role(message) is not None)
async def register_contact(message: Message) -> None:
    """OWNER_USERNAMES / SECOND_CONTACT_USERNAMES pressing /start: remember their chat id for notifications."""
    from bot.pipeline import contacts

    settings = get_settings()
    role = _contact_role(message)
    env_id = (settings.admin_chat_id or (settings.admin_ids[0] if settings.admin_ids else None)) if role == "owner" \
        else settings.second_contact_chat_id
    async with SessionLocal() as session:
        result = await contacts.register(session, role, message.chat.id, message.from_user.username)
        await session.commit()
    if result == "already":
        from aiogram.dispatcher.event.bases import SkipHandler
        raise SkipHandler()  # already registered: show the usual /start menu
    if result == "taken":
        await message.answer("Ця роль уже закріплена за іншим акаунтом. Щоб змінити — задайте ID у змінних середовища "
                             "або видаліть запис у таблиці pipeline_contacts.")
        return
    lines = [f"✅ Вас зареєстровано як: <b>{ROLE_LABELS[role]}</b>.", f"Ваш chat_id: <code>{message.chat.id}</code>"]
    if env_id and env_id != message.chat.id:
        lines.append(f"⚠️ У змінних середовища вже задано інший ID ({env_id}) — сповіщення йдуть туди.")
    else:
        lines.append("Сюди надходитимуть картки запитів з кнопками та нагадування (5/15/60 хв).")
    lines.append("Команди: /sla — зведення, /inq &lt;номер&gt; — картка запиту.")
    await message.answer("\n".join(lines))


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
        if inquiry.client_tg_id is not None and inquiry.client_tg_id != user.id:
            await safe_ack(message, "Цей запит уже прив’язаний до іншого акаунта. Зверніться до менеджера.")
            return
        service.bind_client(inquiry, tg_id=user.id, chat_id=message.chat.id, username=user.username, full_name=user.full_name)
        await service.add_event(session, inquiry.id, "client_bound", "client", f"tg:{user.id}")
        await session.commit()
        await notify.send_owner_card(message.bot, session, inquiry, header="🔗 Клієнт підключив Telegram до запиту",
                                     targets=notify.escalation_targets(1))
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
            from bot.ai import runtime as ai_runtime
            await ai_runtime.set_paused(session, inquiry.client_tg_id, True, "client_requested_manager")
            await session.commit()
            await notify.send_owner_card(callback.bot, session, inquiry, header="🙋 <b>Клієнт кличе менеджера</b>", level=2)
            await session.commit()
        await callback.message.answer(texts.faq_human())
    await callback.answer()


@router.callback_query(F.data.startswith("cli:"))
async def client_decision(callback: CallbackQuery) -> None:
    if callback.message is None or callback.message.chat.type != "private" or callback.message.chat.id != callback.from_user.id:
        await callback.answer("Відкрийте особистий чат із ботом", show_alert=True)
        return
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
                                     targets=notify.escalation_targets(1))
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
