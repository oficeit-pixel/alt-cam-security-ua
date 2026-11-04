"""Owner side: one-tap buttons on inquiry cards, templated replies, relay, TTN, stock, /sla."""
from __future__ import annotations

import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.base import SessionLocal
from bot.db.models import Inquiry, WebOrder
from bot.handlers.admin import is_admin
from bot.integrations import nova_poshta_tracking as np
from bot.integrations.supplier_stock import check_items
from bot.pipeline import delivery, notify, service, texts
from bot.pipeline.statuses import PAYMENT_METHODS, STATUS_ORDER, STATUSES, can_transition, label
from bot.states.states import OwnerPipelineSG

logger = logging.getLogger("altcam.pipeline.owner")
router = Router(name="pipeline_owner")
# Templated reply -> status it implies (applied only when it is a forward move).
TEMPLATE_STATUS = {"chk": "taken", "yes": "stock_checked", "no": "stock_checked", "cnf": "offer_sent"}


def _forward(current: str, target: str) -> bool:
    return (current in STATUS_ORDER and target in STATUS_ORDER
            and STATUS_ORDER.index(target) > STATUS_ORDER.index(current) and can_transition(current, target))


async def _refresh_card(callback: CallbackQuery, session, inquiry: Inquiry, header: str | None = None) -> None:
    order = await session.get(WebOrder, inquiry.web_order_id) if inquiry.web_order_id else None
    try:
        await callback.message.edit_text(notify.owner_card(inquiry, order, header), reply_markup=notify.owner_keyboard(inquiry, order),
                                         disable_web_page_preview=True)
    except Exception:  # message too old / identical content: send a fresh card instead
        await notify.send_owner_card(callback.bot, session, inquiry, header=header, targets=[callback.message.chat.id])


async def send_to_client(bot, session, inquiry: Inquiry, text: str, owner_id: int | None, *, kind: str = "owner_reply",
                         reply_markup=None) -> bool:
    if not await delivery.send_client_text(bot, inquiry, text, reply_markup=reply_markup):
        return False
    await service.record_owner_reply(session, inquiry, text, owner_id, kind=kind)
    if inquiry.status == "new" and can_transition("new", "taken"):
        await service.transition(session, inquiry, "taken", actor="owner", owner_id=owner_id)
    return True


@router.callback_query(F.data.startswith("inq:"))
async def owner_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Тільки для менеджера", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) < 3 or not parts[1].isdigit():
        await callback.answer()
        return
    inquiry_id, action, arg = int(parts[1]), parts[2], (parts[3] if len(parts) > 3 else "")
    owner_id = callback.from_user.id
    async with SessionLocal() as session:
        inquiry = await session.get(Inquiry, inquiry_id)
        if inquiry is None:
            await callback.answer("Запит не знайдено", show_alert=True)
            return
        note = None
        if action == "take":
            if can_transition(inquiry.status, "taken"):
                await service.transition(session, inquiry, "taken", actor="owner", owner_id=owner_id)
            # Business chat: no automatic "taken" message on behalf of the owner (he answers himself).
            sent = False if delivery.is_business(inquiry) else await send_to_client(
                callback.bot, session, inquiry, texts.taken_text(inquiry.id), owner_id, kind="auto_taken")
            if not sent:  # site lead without Telegram: taking still stops the escalation
                await service.record_owner_reply(session, inquiry, "taken (no client chat)", owner_id, kind="taken")
            note = "Взято в роботу" + (" · клієнту надіслано повідомлення" if sent else " · зателефонуйте клієнту")
        elif action == "reply":
            await state.set_state(OwnerPipelineSG.reply_text)
            await state.update_data(inquiry_id=inquiry.id)
            await callback.message.answer(f"✍️ Напишіть відповідь клієнту по запиту №{inquiry.id} (текст/фото). /cancel — скасувати.")
            await callback.answer()
            return
        elif action == "tpl":
            text = texts.template_text(arg, business=delivery.is_business(inquiry))
            if text is None:
                await callback.answer("Невідомий шаблон", show_alert=True)
                return
            markup = notify.client_confirm_keyboard(inquiry.id) if arg == "cnf" else None
            if not await send_to_client(callback.bot, session, inquiry, text, owner_id, kind=f"template:{arg}", reply_markup=markup):
                await callback.answer("Клієнт не в боті — зв’яжіться телефоном", show_alert=True)
                return
            target = TEMPLATE_STATUS.get(arg)
            if target and _forward(inquiry.status, target):
                await service.transition(session, inquiry, target, actor="owner", owner_id=owner_id)
            note = f"Надіслано шаблон: {texts.TEMPLATES[arg][0]}"
        elif action == "st":
            if not can_transition(inquiry.status, arg):
                await callback.answer(f"Не можна: {label(inquiry.status)} → {label(arg)}", show_alert=True)
                return
            await service.transition(session, inquiry, arg, actor="owner", owner_id=owner_id)
            note = f"Статус → {STATUSES.get(arg, arg)}"
        elif action == "pm" and arg in PAYMENT_METHODS:
            if not can_transition(inquiry.status, "paid"):
                await callback.answer(f"Не можна з {label(inquiry.status)}", show_alert=True)
                return
            inquiry.payment_method = arg
            await service.transition(session, inquiry, "paid", actor="owner", owner_id=owner_id, note=PAYMENT_METHODS[arg])
            if arg == "prepay":
                await send_to_client(callback.bot, session, inquiry, texts.template_text("thx"), owner_id, kind="paid_ack")
            note = f"Оплата: {PAYMENT_METHODS[arg]}"
        elif action == "ttn":
            await state.set_state(OwnerPipelineSG.ttn)
            await state.update_data(inquiry_id=inquiry.id)
            await callback.message.answer(f"🚚 Надішліть номер ТТН Нової пошти (14 цифр) для запиту №{inquiry.id}. /cancel — скасувати.")
            await callback.answer()
            return
        elif action == "stock":
            await callback.answer("Перевіряю фіди постачальників…")
            order = await session.get(WebOrder, inquiry.web_order_id) if inquiry.web_order_id else None
            rows = await check_items(order.items if order else [])
            lines = [f"<b>Наявність по запиту №{inquiry.id}</b>"] + [
                f"• {escape(r['name'])} <code>{escape(r['id'])}</code>: <b>{escape(r['stock'])}</b>"
                + (f" — <a href=\"{escape(r['url'])}\">сайт постачальника</a>" if r["url"] else "")
                for r in rows
            ]
            await service.add_event(session, inquiry.id, "stock_check", "owner", "; ".join(f"{r['id']}={r['stock']}" for r in rows))
            await session.commit()
            await callback.message.answer("\n".join(lines) if rows else "У замовленні немає товарів постачальників — перевірте вручну.",
                                          disable_web_page_preview=True)
            return
        elif action != "card":
            await callback.answer()
            return
        await session.commit()
        await _refresh_card(callback, session, inquiry, f"✔️ {note}" if note else None)
        await session.commit()
    await callback.answer(note or "")


@router.message(Command("cancel"), StateFilter(OwnerPipelineSG.reply_text, OwnerPipelineSG.ttn))
async def owner_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Скасовано.")


@router.message(StateFilter(OwnerPipelineSG.reply_text))
async def owner_reply_text(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    inquiry_id = (await state.get_data()).get("inquiry_id")
    await state.clear()
    await relay_owner_message(message, inquiry_id)


async def relay_owner_message(message: Message, inquiry_id: int | None) -> None:
    async with SessionLocal() as session:
        inquiry = await session.get(Inquiry, inquiry_id) if inquiry_id else None
        if inquiry is None or not inquiry.client_chat_id:
            await message.answer("Не вдалося: клієнт не підключений до бота.")
            return
        try:
            if delivery.is_business(inquiry):
                if not message.text:
                    await message.answer("Медіа у бізнес-чат надішліть напряму з вашого акаунта; тут — лише текст.")
                    return
                if not await delivery.send_client_text(message.bot, inquiry, message.html_text):
                    raise RuntimeError("business_send_failed")
            else:
                await message.bot.copy_message(inquiry.client_chat_id, message.chat.id, message.message_id)
        except Exception as exc:
            await message.answer(f"Не вдалося надіслати ({type(exc).__name__}).")
            return
        await service.record_owner_reply(session, inquiry, message.text or message.caption or "[медіа]", message.from_user.id)
        if inquiry.status == "new":
            await service.transition(session, inquiry, "taken", actor="owner", owner_id=message.from_user.id)
        await session.commit()
    await message.answer(f"✅ Надіслано клієнту (запит №{inquiry_id}).")


@router.message(StateFilter(OwnerPipelineSG.ttn))
async def owner_ttn(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    ttn = np.normalize_ttn(message.text or "")
    if ttn is None:
        await message.answer("ТТН має містити 14 цифр. Спробуйте ще раз або /cancel.")
        return
    inquiry_id = (await state.get_data()).get("inquiry_id")
    await state.clear()
    async with SessionLocal() as session:
        inquiry = await session.get(Inquiry, inquiry_id) if inquiry_id else None
        if inquiry is None:
            await message.answer("Запит не знайдено.")
            return
        inquiry.ttn = ttn
        if can_transition(inquiry.status, "shipped"):
            await service.transition(session, inquiry, "shipped", actor="owner", owner_id=message.from_user.id)
        sent = await send_to_client(message.bot, session, inquiry, texts.shipped_text(ttn), message.from_user.id, kind="ttn")
        await session.commit()
        await notify.send_owner_card(message.bot, session, inquiry, header="🚚 ТТН збережено" + (" і надіслано клієнту" if sent else ""),
                                     targets=[message.chat.id])
        await session.commit()


@router.message(F.reply_to_message, StateFilter(None), ~F.text.startswith("/"))
async def owner_reply_by_quote(message: Message) -> None:
    """Owner just replies (swipe-reply) to a card or a copied client message -> relay to the client."""
    if message.from_user is None or not is_admin(message.from_user.id):
        from aiogram.dispatcher.event.bases import SkipHandler
        raise SkipHandler()
    async with SessionLocal() as session:
        inquiry = await service.inquiry_by_owner_message(session, message.chat.id, message.reply_to_message.message_id)
    if inquiry is None:
        from aiogram.dispatcher.event.bases import SkipHandler
        raise SkipHandler()
    await relay_owner_message(message, inquiry.id)


@router.message(Command("sla"))
async def sla(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    now = service.utcnow()
    async with SessionLocal() as session:
        items = await service.open_inquiries(session, limit=30)
    summary = service.sla_summary(items, now)
    lines = [
        "<b>SLA — відкриті запити</b>",
        f"Відкритих: {summary['open']} · чекають відповіді: {summary['waiting']} "
        f"(>15 хв: {summary['waiting_over_15m']}, >1 год: {summary['waiting_over_1h']}) · нових не взято: {summary['new_not_taken']}",
        "",
    ]
    buttons = []
    for inquiry in items[:20]:
        wait = f"⏱{int((now - inquiry.awaiting_since).total_seconds() // 60)}хв " if inquiry.awaiting_since else ""
        who = inquiry.client_name or inquiry.client_username or inquiry.phone or "—"
        lines.append(f"№{inquiry.id} {wait}{escape(label(inquiry.status))} · {escape(who[:40])}")
        buttons.append(InlineKeyboardButton(text=f"№{inquiry.id}", callback_data=f"inq:{inquiry.id}:card"))
    rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
    await message.answer("\n".join(lines) if items else "Відкритих запитів немає 🎉",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows) if rows else None)


@router.message(Command("inq"))
async def inquiry_card(message: Message, command: CommandObject) -> None:
    if not is_admin(message.from_user.id):
        return
    if not (command.args or "").strip().isdigit():
        await message.answer("Використання: /inq 123")
        return
    async with SessionLocal() as session:
        inquiry = await session.get(Inquiry, int(command.args.strip()))
        if inquiry is None:
            await message.answer("Запит не знайдено.")
            return
        await notify.send_owner_card(message.bot, session, inquiry, targets=[message.chat.id])
        await session.commit()
