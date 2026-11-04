"""Telegram rendering for the pipeline: owner cards, keyboards, escalation fan-out."""
from __future__ import annotations

import logging
from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.db.models import Inquiry, WebOrder
from bot.pipeline import service
from bot.pipeline.statuses import PAYMENT_METHODS, STATUSES, label, next_actions
from bot.pipeline.texts import TEMPLATES

logger = logging.getLogger("altcam.pipeline")
SOURCE_LABELS = {"bot": "Telegram-бот", "site_lead": "Заявка з сайту", "site_order": "Кошик на сайті", "business": "Особистий Telegram",
                 "telegram_business": "Особистий Telegram (Business)"}
LEVEL_LABELS = {1: "⏰ Нагадування", 2: "⚠️ Клієнт чекає", 3: "🚨 КЛІЄНТ ЧЕКАЄ ДОВГО"}


def supplier_codes(order: WebOrder | None) -> list[str]:
    codes: list[str] = []
    for item in (order.items if order else None) or []:
        code = str(item.get("id", "")).partition("-")[0].casefold() if isinstance(item, dict) else ""
        if code in {"viatec", "yugtorg"} and code not in codes:
            codes.append(code)
    return codes


def owner_card(inquiry: Inquiry, order: WebOrder | None = None, header: str | None = None, now=None) -> str:
    now = now or service.utcnow()
    lines = [header] if header else []
    lines.append(f"<b>Запит №{inquiry.id}</b> · {escape(SOURCE_LABELS.get(inquiry.source, inquiry.source))}")
    lines.append(f"Статус: <b>{escape(label(inquiry.status))}</b>")
    who = " ".join(filter(None, [
        escape(inquiry.client_name or ""),
        f"@{escape(inquiry.client_username)}" if inquiry.client_username else "",
        f"<code>{escape(inquiry.phone)}</code>" if inquiry.phone else "",
    ]))
    if who:
        lines.append(f"Клієнт: {who}")
    if order is not None:
        lines.append(f"Замовлення: <b>{escape(order.order_number)}</b> · {float(order.subtotal or 0):.2f} ₴")
        for index, item in enumerate((order.items or [])[:10], 1):
            if isinstance(item, dict):
                lines.append(f"  {index}. {escape(str(item.get('name', ''))[:120])} × {item.get('quantity', 1)} <code>{escape(str(item.get('id', '')))}</code>")
        delivery = order.delivery or {}
        if delivery.get("label"):
            lines.append(f"Доставка: {escape(str(delivery.get('label'))[:200])}")
    if inquiry.payment_method:
        lines.append(f"Оплата: {escape(PAYMENT_METHODS.get(inquiry.payment_method, inquiry.payment_method))}")
    if inquiry.ttn:
        lines.append(f"ТТН: <code>{escape(inquiry.ttn)}</code>")
    if inquiry.awaiting_since:
        lines.append(f"⏱ Чекає відповіді: {int((now - inquiry.awaiting_since).total_seconds() // 60)} хв")
    if inquiry.summary:
        lines.extend(["", escape(inquiry.summary[:1500])])
    return "\n".join(lines)[:4000]


def owner_keyboard(inquiry: Inquiry, order: WebOrder | None = None) -> InlineKeyboardMarkup:
    p = f"inq:{inquiry.id}"
    rows: list[list[InlineKeyboardButton]] = []
    first = []
    if inquiry.status == "new":
        first.append(InlineKeyboardButton(text="👤 Взяти в роботу", callback_data=f"{p}:take"))
    if inquiry.client_chat_id:
        first.append(InlineKeyboardButton(text="✍️ Відповісти", callback_data=f"{p}:reply"))
    if first:
        rows.append(first)
    if inquiry.client_chat_id and inquiry.status not in {"closed", "rejected"}:
        keys = list(TEMPLATES)
        for start in range(0, len(keys), 2):
            rows.append([InlineKeyboardButton(text=TEMPLATES[key][0], callback_data=f"{p}:tpl:{key}") for key in keys[start:start + 2]])
    tools = []
    if supplier_codes(order) and inquiry.status not in {"closed", "rejected"}:
        tools.append(InlineKeyboardButton(text="🔎 Наявність у постачальника", callback_data=f"{p}:stock"))
    if inquiry.status in {"paid", "supplier_ordered", "supplier_paid"}:
        tools.append(InlineKeyboardButton(text="🚚 Ввести ТТН", callback_data=f"{p}:ttn"))
    if tools:
        rows.append(tools)
    if inquiry.status in {"confirmed", "offer_sent"}:
        rows.append([
            InlineKeyboardButton(text="💳 Оплачено (передоплата)", callback_data=f"{p}:pm:prepay"),
            InlineKeyboardButton(text="📮 НП (накладений)", callback_data=f"{p}:pm:cod"),
        ])
    status_buttons = [
        InlineKeyboardButton(text=STATUSES[s], callback_data=f"{p}:st:{s}")
        for s in next_actions(inquiry.status) if s != "paid" and not (s == "taken" and inquiry.status == "new")
    ]
    for start in range(0, len(status_buttons), 2):
        rows.append(status_buttons[start:start + 2])
    rows.append([InlineKeyboardButton(text="🔄 Оновити картку", callback_data=f"{p}:card")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def client_faq_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплата", callback_data="faq:pay"),
         InlineKeyboardButton(text="🚚 Доставка", callback_data="faq:dlv"),
         InlineKeyboardButton(text="🛡 Гарантія", callback_data="faq:war")],
        [InlineKeyboardButton(text="🙋 Покликати менеджера", callback_data="faq:human")],
    ])


def client_confirm_keyboard(inquiry_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтверджую замовлення", callback_data=f"cli:{inquiry_id}:ok")],
        [InlineKeyboardButton(text="❓ Є питання", callback_data=f"cli:{inquiry_id}:q"),
         InlineKeyboardButton(text="❌ Неактуально", callback_data=f"cli:{inquiry_id}:no")],
    ])


def escalation_targets(level: int) -> list[int]:
    settings = get_settings()
    targets: list[int] = []
    for chat_id, min_level in ((getattr(settings, "managers_chat_id", None), 1), (settings.owner_chat_id, 1), (settings.second_contact_target, 2), (settings.site_lead_group_id, 3)):
        if chat_id and level >= min_level and chat_id not in targets:
            targets.append(chat_id)
    return targets


async def send_owner_card(bot, session: AsyncSession, inquiry: Inquiry, *, header: str | None = None, level: int = 1,
                          targets: list[int] | None = None) -> int:
    """Send the card with action buttons; log owner message ids so plain replies map back to the inquiry."""
    if bot is None:
        return 0
    order = await session.get(WebOrder, inquiry.web_order_id) if inquiry.web_order_id else None
    text, keyboard = owner_card(inquiry, order, header), owner_keyboard(inquiry, order)
    sent = 0
    for chat_id in targets if targets is not None else escalation_targets(level):
        try:
            message = await bot.send_message(chat_id, text, reply_markup=keyboard, disable_web_page_preview=True)
        except Exception as exc:  # never break capture because Telegram failed
            logger.warning("owner_notify_failed inquiry=%s chat=%s (%s)", inquiry.id, chat_id, type(exc).__name__)
            continue
        await service.add_event(session, inquiry.id, "owner_notified", "system", header, owner_chat_id=chat_id,
                                owner_message_id=message.message_id)
        sent += 1
    return sent
