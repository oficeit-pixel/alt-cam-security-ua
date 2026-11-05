"""Website chat endpoint -> the same consultant (fake LLM, no network, no DB)."""
import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot.ai.consultant import Consultant
from bot.config import get_settings
from bot.web import ai_chat


class FakeLLM:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    async def chat(self, messages, tools=None):
        self.calls.append(messages)
        return self.replies.pop(0)


def run_with_client(coro_factory):
    async def runner():
        app = web.Application()
        app["rate_limits"] = {}
        ai_chat.register_ai_chat_routes(app)
        async with TestClient(TestServer(app)) as client:
            return await coro_factory(client)
    return asyncio.run(runner())


@pytest.fixture
def enabled(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", True)
    monkeypatch.setattr(settings, "llm_api_key", "fake")
    monkeypatch.setattr(settings, "ai_web_rate_per_minute", 3)
    yield settings
    ai_chat.set_consultant_factory(None)


def test_disabled_without_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", None)

    async def go(client):
        status = await (await client.get("/api/ai/status")).json()
        response = await client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "привіт"}]})
        return status, response.status
    status, code = run_with_client(go)
    assert status == {"enabled": False} and code == 503


def test_reply_intro_language_and_rate_limit(enabled):
    fake = FakeLLM([{"role": "assistant", "content": "Подскажите, улица или помещение?"},
                    {"role": "assistant", "content": "Для вулиці — циліндричні камери."}])

    async def factory():
        return Consultant(fake)
    ai_chat.set_consultant_factory(factory)

    async def go(client):
        first = await (await client.post("/api/ai/chat", json={"messages": [
            {"role": "user", "content": "Здравствуйте, нужно 4 камеры"}]})).json()
        second = await (await client.post("/api/ai/chat", json={"messages": [
            {"role": "user", "content": "Потрібно 4 камери"}, {"role": "assistant", "content": "Де?"},
            {"role": "user", "content": "На вулицю"}]})).json()
        bad = (await client.post("/api/ai/chat", json={"messages": [{"role": "system", "content": "x"}]})).status
        limited = (await client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "ще"}]})).status
        return first, second, bad, limited
    first, second, bad, limited = run_with_client(go)
    assert first["ok"] and first["reply"].startswith("Здравствуйте! Это ALT-CAM Security") and "бот" not in first["reply"]
    assert second["reply"] == "Для вулиці — циліндричні камери."           # no repeated intro
    assert bad == 400 and limited == 429
    assert fake.calls[0][0]["role"] == "system"                            # same system prompt as Telegram


def test_handoff_shows_contact_form(enabled):
    async def factory():
        return Consultant(FakeLLM([]))
    ai_chat.set_consultant_factory(factory)

    async def go(client):
        return await (await client.post("/api/ai/chat", json={"messages": [
            {"role": "user", "content": "Скиньте реквізити, я готовий оплатити"}]})).json()
    data = run_with_client(go)
    assert data["handoff"] == "payment" and "менеджер" in data["reply"]
    assert data["telegram_link"].startswith("https://t.me/") and data["telegram_link"].endswith("?start=site")


def test_llm_failure_never_breaks_site(enabled):
    from bot.ai.llm import LLMUnavailable

    class Broken:
        async def chat(self, *_):
            raise LLMUnavailable("rate_limited")

    async def factory():
        return Consultant(Broken())
    ai_chat.set_consultant_factory(factory)

    async def go(client):
        response = await client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "Скільки коштує камера?"}]})
        return response.status, await response.json()
    code, data = run_with_client(go)
    assert code == 200 and data["handoff"] == "ai_unavailable" and data["reply"]


def test_cart_url_returned_with_kit_reply(enabled):
    from bot.ai.catalog import Product

    cam = Product(id="viatec-1", name="IP відеокамера 4МП PoE", model="IPC", brand="Dahua",
                  category="Камери відеоспостереження", price=1525.0)
    fake = FakeLLM([
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
            "name": "create_cart_link", "arguments": '{"items": [{"id": "viatec-1", "qty": 2}]}'}}]},
        {"role": "assistant", "content": "2 камеры по 1 525 грн.\nИтого: 3 050 грн."},
    ])

    async def factory():
        return Consultant(fake, product_catalog={cam.id: cam})
    ai_chat.set_consultant_factory(factory)

    async def go(client):
        return await (await client.post("/api/ai/chat", json={"messages": [
            {"role": "user", "content": "Нужно 2 камеры"}]})).json()
    data = run_with_client(go)
    assert "handoff" not in data and data["cart_url"] == "https://alt-cam.net.ua/catalog.html?cart=viatec-1:2"
    assert data["cart_url"] in data["reply"] and "3 050 грн" in data["reply"]


def test_cart_url_parsed_from_reply_text(enabled):
    url = "https://alt-cam.net.ua/catalog.html?cart=viatec-1:2"

    class Stub:
        async def reply(self, history):
            from bot.ai.consultant import ConsultResult
            return ConsultResult(text=f"Корзина: {url}")

    async def factory():
        return Stub()
    ai_chat.set_consultant_factory(factory)

    async def go(client):
        return await (await client.post("/api/ai/chat", json={"messages": [
            {"role": "user", "content": "Ссылка на корзину"}]})).json()
    assert run_with_client(go)["cart_url"] == url
