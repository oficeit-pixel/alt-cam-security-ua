"""Website chat widget -> the same AI consultant that answers in the Telegram bot and Telegram Business chats.

Stateless: the widget keeps the short conversation in the browser and sends it with every request; the server
validates it, rate-limits per IP and runs `bot.ai.consultant.Consultant` (same prompt, tools, price guards,
hand-off triggers). Disabled (404-like `enabled: false`) unless AI_CONSULTANT_ENABLED=true and GEMINI_API_KEY is set,
so the widget simply stays hidden and the site keeps its usual forms.
"""
from __future__ import annotations

import asyncio
import logging
from time import monotonic
from typing import Any

from aiohttp import web

from bot.config import get_settings

logger = logging.getLogger("altcam.ai.web")
MAX_TURNS = 12
MAX_CHARS = 1500
_factory = None  # tests inject: async () -> Consultant


def set_consultant_factory(factory) -> None:
    global _factory
    _factory = factory


def _cors(request: web.Request) -> dict[str, str]:
    from bot.web.site_leads import _cors_headers

    return _cors_headers(request)


def _limited(request: web.Request, limit: int, window: int = 60) -> bool:
    store = request.app["rate_limits"]
    key = "ai:" + (request.remote or "unknown")
    now = monotonic()
    attempts = [stamp for stamp in store.get(key, []) if now - stamp < window]
    store[key] = attempts
    if len(attempts) >= limit:
        return True
    attempts.append(now)
    return False


def parse_history(payload: Any) -> list[dict[str, str]]:
    messages = payload.get("messages") if isinstance(payload, dict) else None
    if not isinstance(messages, list) or not messages:
        raise ValueError("invalid_messages")
    history = []
    for item in messages[-MAX_TURNS:]:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
            raise ValueError("invalid_messages")
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("invalid_messages")
        history.append({"role": item["role"], "content": content.strip()[:MAX_CHARS]})
    if history[-1]["role"] != "user":
        raise ValueError("invalid_messages")
    return history


async def _overrides() -> dict[str, float]:
    try:
        from sqlalchemy import select

        from bot.db.base import SessionLocal
        from bot.db.models import PriceOverride

        async with SessionLocal() as session:
            rows = (await asyncio.wait_for(session.scalars(
                select(PriceOverride).where(PriceOverride.enabled.is_(True))), timeout=5)).all()
        return {row.product_id: float(row.price_uah) for row in rows}
    except Exception as exc:  # DB down: catalog prices still work
        logger.warning("ai_web_overrides_unavailable (%s)", type(exc).__name__)
        return {}


async def _consultant():
    if _factory is not None:
        return await _factory()
    from bot.ai.consultant import Consultant
    from bot.ai.llm import LLMClient

    settings = get_settings()
    return Consultant(LLMClient.from_settings(settings), overrides=await _overrides(),
                      site_origin=settings.site_public_origin, max_rounds=settings.ai_max_tool_rounds)


def _handoff_text(lang: str) -> str:
    if lang == "ru":
        return ("Этот вопрос лучше решит менеджер ALT-CAM. Оставьте телефон в форме ниже или напишите нам в Telegram — "
                "ответим в ближайшее время в рабочие часы.")
    return ("Це питання краще вирішить менеджер ALT-CAM. Залиште телефон у формі нижче або напишіть нам у Telegram — "
            "відповімо найближчим часом у робочий час.")


async def ai_status(request: web.Request) -> web.Response:
    return web.json_response({"enabled": get_settings().ai_web_active}, headers=_cors(request))


async def ai_chat(request: web.Request) -> web.Response:
    from bot.ai.consultant import conversation_language, intro

    settings = get_settings()
    headers = _cors(request)
    if not settings.ai_web_active:
        return web.json_response({"ok": False, "enabled": False, "error": "disabled"}, status=503, headers=headers)
    if _limited(request, max(1, settings.ai_web_rate_per_minute)):
        return web.json_response({"ok": False, "error": "rate_limited"}, status=429, headers=headers)
    try:
        history = parse_history(await request.json())
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_messages"}, status=400, headers=headers)
    lang = conversation_language(history)
    telegram = f"https://t.me/{settings.bot_username}?start=site"
    try:
        result = await asyncio.wait_for((await _consultant()).reply(history), timeout=settings.ai_timeout_seconds + 30)
    except Exception as exc:  # never break the site because of AI
        logger.warning("ai_web_failed (%s)", type(exc).__name__)
        return web.json_response({"ok": True, "reply": _handoff_text(lang), "handoff": "ai_unavailable",
                                  "telegram_link": telegram}, headers=headers)
    if result.text and not result.handoff:
        introduced = any(m["role"] == "assistant" for m in history)
        text = result.text if introduced or "alt-cam" in result.text.lower()[:120] else \
            f"{intro(lang, settings.ai_disclose_bot)}\n\n{result.text}"
        return web.json_response({"ok": True, "reply": text, "cart_url": result.cart_url}, headers=headers)
    reply = (result.text + "\n\n" if result.text else "") + _handoff_text(lang)
    return web.json_response({"ok": True, "reply": reply, "handoff": result.handoff or "other",
                              "cart_url": result.cart_url, "telegram_link": telegram},
                             headers=headers)


def register_ai_chat_routes(app: web.Application) -> None:
    app.router.add_get("/api/ai/status", ai_status)
    app.router.add_post("/api/ai/chat", ai_chat)
