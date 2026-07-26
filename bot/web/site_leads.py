from html import escape
from typing import Any

from aiohttp import web
from aiogram import Bot

from bot.config import get_settings


def _cors_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "Access-Control-Allow-Origin": settings.site_public_origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
    }


def _clean(value: Any, fallback: str = "Не вказано") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _lead_text(payload: dict[str, Any]) -> str:
    lead_type = _clean(payload.get("type"))
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    quote = payload.get("quote") if isinstance(payload.get("quote"), dict) else {}
    message = _clean(payload.get("message"))
    source = _clean(payload.get("source"))

    lines = [
        "<b>Нова заявка з сайту ALT-CAM</b>",
        "",
        f"Тип: <b>{escape(lead_type)}</b>",
        f"Джерело: {escape(source)}",
    ]

    if client:
        lines.extend(
            [
                "",
                "<b>Клієнт</b>",
                f"Ім'я: <b>{escape(_clean(client.get('name')))}</b>",
                f"Телефон: <code>{escape(_clean(client.get('phone')))}</code>",
                f"Email: {escape(_clean(client.get('email')))}",
                f"Бажана дата: {escape(_clean(client.get('date')))}",
                f"Коментар: {escape(_clean(client.get('comment')))}",
            ]
        )

    if quote:
        lines.extend(
            [
                "",
                "<b>Розрахунок</b>",
                f"Напрямок: <b>{escape(_clean(quote.get('type')))}</b>",
                f"Сума: <b>{escape(_clean(quote.get('total')))} грн</b>",
                f"Знижка: {escape(_clean(quote.get('discount')))} грн",
                f"Завдаток: {escape(_clean(quote.get('deposit')))} грн",
            ]
        )

    lines.extend(["", "<b>Деталі з калькулятора</b>", f"<pre>{escape(message)}</pre>"])
    return "\n".join(lines)


async def site_lead_options(_: web.Request) -> web.Response:
    return web.Response(status=204, headers=_cors_headers())


async def site_lead(request: web.Request) -> web.Response:
    settings = get_settings()
    bot: Bot = request.app["bot"]
    try:
        payload = await request.json()
    except Exception:
        return web.json_response(
            {"ok": False, "error": "invalid_json"},
            status=400,
            headers=_cors_headers(),
        )

    text = _lead_text(payload)
    targets = [settings.admin_chat_id]
    if settings.site_lead_group_id and settings.site_lead_group_id not in targets:
        targets.append(settings.site_lead_group_id)

    for chat_id in targets:
        await bot.send_message(chat_id, text[:4096])

    return web.json_response({"ok": True}, headers=_cors_headers())


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "alt-cam-bot"})


async def start_site_lead_server(bot: Bot) -> web.AppRunner:
    settings = get_settings()
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_options("/site-lead", site_lead_options)
    app.router.add_post("/site-lead", site_lead)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.http_host, settings.http_port)
    await site.start()
    return runner
