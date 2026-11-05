"""Glue between the consultant and the order pipeline (bot chat and Telegram Business chat)."""
from __future__ import annotations

import logging
from datetime import timedelta
from html import escape
from typing import Any

from sqlalchemy import select

from bot.ai.consultant import HANDOFF_REASONS, Consultant, business_prefix, conversation_language, detect_language, intro  # noqa: F401 (detect_language re-exported)
from bot.ai.llm import LLMClient
from bot.config import get_settings
from bot.db.models import AIChatPref, Inquiry, InquiryEvent, PriceOverride
from bot.pipeline import delivery, notify, schedule, service

logger = logging.getLogger("altcam.ai.runtime")
USER_KINDS = {"created", "client_message"}
ASSISTANT_KINDS = {"ai_reply"}
OWNER_KINDS = {"owner_reply", "owner_business_reply", "auto_taken", "paid_ack", "ttn"}
_factory = None  # tests inject a fake consultant factory: (session) -> Consultant


def set_consultant_factory(factory) -> None:
    global _factory
    _factory = factory


async def is_paused(session, client_tg_id: int | None) -> bool:
    if not client_tg_id:
        return True
    pref = await session.get(AIChatPref, client_tg_id, populate_existing=True)
    return bool(pref and pref.paused)


async def set_paused(session, client_tg_id: int, paused: bool, reason: str | None = None) -> None:
    pref = await session.get(AIChatPref, client_tg_id)
    if pref is None:
        pref = AIChatPref(client_tg_id=client_tg_id)
        session.add(pref)
    pref.paused, pref.reason = paused, (reason or "")[:64] or None
    await session.flush()


async def history(session, inquiry_id: int, limit: int = 14) -> tuple[list[dict[str, str]], bool]:
    rows = (await session.scalars(
        select(InquiryEvent).where(InquiryEvent.inquiry_id == inquiry_id).order_by(InquiryEvent.id.desc()).limit(60)
    )).all()
    messages, introduced = [], False
    for event in reversed(rows):
        text = (event.text or "").strip()
        if event.kind in ASSISTANT_KINDS:
            introduced = True
        if not text:
            continue
        if event.kind in USER_KINDS:
            messages.append({"role": "user", "content": text[:2000]})
        elif event.kind in ASSISTANT_KINDS:
            messages.append({"role": "assistant", "content": text[:2000]})
        elif event.kind in OWNER_KINDS or event.kind.startswith("template:"):
            messages.append({"role": "assistant", "content": f"(Відповідь менеджера) {text[:1500]}"})
    return messages[-limit:], introduced


async def _overrides(session) -> dict[str, float]:
    rows = (await session.scalars(select(PriceOverride).where(PriceOverride.enabled.is_(True)))).all()
    return {row.product_id: float(row.price_uah) for row in rows}


async def _consultant(session) -> Consultant:
    if _factory is not None:
        return await _factory(session)
    settings = get_settings()
    return Consultant(LLMClient.from_settings(settings), overrides=await _overrides(session),
                      site_origin=settings.site_public_origin, max_rounds=settings.ai_max_tool_rounds)


def handoff_client_text(now=None, lang: str = "uk") -> str:
    if lang == "ru":
        return "Передаю ваш вопрос менеджеру ALT-CAM — он ответит в ближайшее время в рабочие часы."
    return f"Передаю ваше питання менеджеру ALT-CAM — він відповість {schedule.eta_text(now)}."


async def respond(bot, session, inquiry: Inquiry, *, business: bool = False, now=None) -> str:
    """Returns 'disabled' | 'paused' | 'replied' | 'handoff' | 'failed' (LLM unavailable: caller uses the standard
    auto-reply, the owner is alerted). Never raises."""
    settings = get_settings()
    if not settings.ai_active or (business and not settings.ai_business_enabled):
        return "disabled"
    if await is_paused(session, inquiry.client_tg_id):
        return "paused"
    msgs, introduced = await history(session, inquiry.id)
    if not msgs or msgs[-1]["role"] != "user":
        return "disabled"
    lang = conversation_language(msgs)
    prefix = business_prefix(settings.ai_disclose_bot)
    if bot is not None and not business:
        try:
            await bot.send_chat_action(inquiry.client_chat_id, "typing")
        except Exception:
            pass
    try:
        result = await (await _consultant(session)).reply(msgs)
    except Exception as exc:  # never lose the client because of AI
        logger.exception("consultant_crashed inquiry=%s (%s)", inquiry.id, type(exc).__name__)
        from bot.ai.consultant import ConsultResult
        result = ConsultResult(text=None, handoff="ai_unavailable")
    # A manager may have taken over while the LLM request was in flight.
    if await is_paused(session, inquiry.client_tg_id):
        return "paused"
    sent_text = None
    if result.text:
        greeting = intro(lang, settings.ai_disclose_bot)
        body = result.text if introduced or "alt-cam" in result.text.lower()[:120] else f"{greeting}\n\n{result.text}"
        sent_text = escape((prefix + body) if business else body, quote=False)
        markup = None if business else notify.client_faq_keyboard()
        if await delivery.send_client_text(bot, inquiry, sent_text, reply_markup=markup):
            await service.add_event(session, inquiry.id, "ai_reply", "ai", result.text)
            await notify.mirror_manager_text(bot, session, inquiry, body, "🤖 Відповідь ШІ")
            if settings.ai_counts_as_response and not result.handoff:
                inquiry.awaiting_since, inquiry.reminder_level = None, 0
        else:
            sent_text = None
    if result.handoff == "ai_unavailable" and not sent_text:
        await service.add_event(session, inquiry.id, "ai_unavailable", "ai", result.handoff_summary)
        if inquiry.awaiting_since is None:
            inquiry.awaiting_since = now or service.utcnow()
        await session.commit()
        for owner in notify.escalation_targets(1):
            if await service.card_is_stale(session, inquiry.id, owner, timedelta(minutes=10)):
                await notify.send_owner_card(bot, session, inquiry, header="⚠️ AI недоступний (ліміт/помилка) — відповідайте самі",
                                             targets=[owner])
        await session.commit()
        return "failed"
    if result.handoff:
        await _handoff(bot, session, inquiry, result.handoff, result.handoff_summary, business=business,
                       client_notified=bool(sent_text), now=now, lang=lang)
        await session.commit()
        return "handoff"
    await session.commit()
    return "replied" if sent_text else "handoff"


async def _handoff(bot, session, inquiry: Inquiry, reason: str, summary: str | None, *, business: bool,
                   client_notified: bool, now=None, lang: str = "uk") -> None:
    label = HANDOFF_REASONS.get(reason, reason)
    await set_paused(session, inquiry.client_tg_id, True, f"handoff:{reason}")
    await service.add_event(session, inquiry.id, "ai_handoff", "ai", f"{reason}: {summary or ''}"[:1000])
    if inquiry.awaiting_since is None:
        inquiry.awaiting_since = now or service.utcnow()
    inquiry.reminder_level = 0
    if not client_notified:
        text = handoff_client_text(now, lang)
        await delivery.send_client_text(bot, inquiry, (business_prefix(get_settings().ai_disclose_bot) + text) if business else text)
    await session.commit()
    header = f"🤖➡️👤 <b>AI передає розмову</b>: {escape(label)}" + (f"\n<i>{escape(summary[:300])}</i>" if summary else "") + \
        "\nAI у цьому чаті вимкнено (/ai_on — увімкнути)."
    level = 2 if reason in {"payment", "angry", "explicit"} else 1
    await notify.send_owner_card(bot, session, inquiry, header=header, level=level)


async def pause_from_owner(session, inquiry: Inquiry, paused: bool, reason: str) -> dict[str, Any]:
    await set_paused(session, inquiry.client_tg_id, paused, reason)
    await service.add_event(session, inquiry.id, "ai_paused" if paused else "ai_resumed", "owner", reason)
    return {"client_tg_id": inquiry.client_tg_id, "paused": paused}
