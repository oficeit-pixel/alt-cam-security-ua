"""AI consultant unit tests: catalog tools, guards, hand-off triggers, mocked LLM (no network)."""
import asyncio
import json

import pytest

from bot.ai import catalog, consultant, llm, policies
from bot.ai.catalog import Product
from bot.ai.consultant import Consultant, detect_handoff, unverified_prices


def make(pid, name, model="", category="Камери відеоспостереження", brand="Dahua", price=1000.0, features=()):
    p = Product(id=pid, name=name, model=model, brand=brand, category=category, features=list(features), price=price)
    p.text = " ".join([p.name, p.model, p.brand, p.category, *p.features]).lower()
    return p


CATALOG = {p.id: p for p in [
    make("viatec-1", "IP відеокамера 4МП PoE", "DH-IPC-HFW1430", price=1525.0),
    make("viatec-2", "IP відеокамера Wi-Fi 4МП", "Imou Ranger", price=900.0),
    make("viatec-3", "AHD камера 2МП", "HAC-1200", price=500.0),
    make("viatec-10", "4-канальний PoE IP відеореєстратор", "DHI-NVR1104HS-P", "Відеореєстратори та накопичувачі", price=6060.0),
    make("viatec-11", "8-канальний IP відеореєстратор", "DHI-NVR1108", "Відеореєстратори та накопичувачі", price=4000.0),
    make("viatec-12", "4-канальний XVR відеореєстратор", "XVR4104", "Відеореєстратори та накопичувачі", price=2000.0),
    make("viatec-20", "Жорсткий диск", "WD Purple 2TB", "Відеореєстратори та накопичувачі", brand="WD", price=3000.0),
    make("viatec-30", "POE комутатор 4 POE + 2 RJ45", "Merlion", "Мережеве обладнання", brand="Merlion", price=900.0),
    make("viatec-40", "Кабель КНП UTP для зовн. робіт, 100м", "Ritar", "Кабельна продукція", brand="Ritar", price=700.0),
    make("viatec-50", "Кронштейн", "PFA", "Кронштейни та монтажні коробки", price=None),
]}


def test_search_uses_catalog_prices_and_overrides():
    rows = catalog.search("камера 4мп poe", catalog=CATALOG)
    assert rows[0]["id"] == "viatec-1" and rows[0]["price_uah"] == 1525.0
    rows = catalog.search("камера 4мп poe", catalog=CATALOG, overrides={"viatec-1": 1490})
    assert rows[0]["price_uah"] == 1490
    assert catalog.search("", catalog=CATALOG) == []


def test_build_kit_picks_ip_poe_components():
    kit = catalog.build_kit(4, catalog=CATALOG)["components"]
    assert [r["id"] for r in kit["cameras"]] == ["viatec-1"]          # no Wi-Fi, no AHD
    assert kit["cameras"][0]["qty"] == 4
    assert [r["id"] for r in kit["nvr"]][0] == "viatec-10"            # 4ch PoE first, XVR excluded
    assert "viatec-12" not in [r["id"] for r in kit["nvr"]]
    assert kit["hdd"][0]["id"] == "viatec-20" and kit["poe_switch"][0]["id"] == "viatec-30"
    assert kit["cable"][0]["qty"] == 1                                  # 4 cams * 25 m -> one 100 m roll
    kit8 = catalog.build_kit(8, catalog=CATALOG)["components"]
    assert [r["id"] for r in kit8["nvr"]] == ["viatec-11"] and kit8["poe_switch"] == []


def test_cart_link_validates_ids_and_totals():
    link = catalog.cart_link([{"id": "viatec-1", "qty": 4}, {"id": "viatec-10"}, {"id": "nope"}, {"id": "a b"}], catalog=CATALOG)
    assert link["ok"] and link["url"] == "https://alt-cam.net.ua/catalog.html?cart=viatec-1:4,viatec-10:1"
    assert link["total_uah"] == 1525 * 4 + 6060 and link["unknown_ids"] == ["nope", "a b"]
    assert catalog.cart_link([{"id": "viatec-50"}], catalog=CATALOG)["total_uah"] is None  # no price -> no total
    assert not catalog.cart_link([{"id": "nope"}], catalog=CATALOG)["ok"]


def test_real_catalog_kit_when_available():
    try:
        products = catalog.products()
    except (OSError, ValueError):
        pytest.skip("catalog-data.js not available")
    assert len(products) > 1000
    assert not any(catalog.HIDDEN_BRANDS.match(p.brand) for p in products.values())
    kit = catalog.build_kit(4)["components"]
    for name in ("cameras", "nvr", "hdd", "poe_switch", "cable"):
        assert kit[name], name
        assert all(r["price_uah"] and r["id"] in products for r in kit[name])


@pytest.mark.parametrize("text,reason", [
    ("Скиньте реквізити, я готовий оплатити", "payment"),
    ("Як оплатити замовлення?", "payment"),
    ("Можна поговорити з менеджером?", "explicit"),
    ("Це обман, верніть гроші!!!", "angry"),
    ("ВИ ДЕ ПРОПАЛИ ДОСІ НЕМАЄ ВІДПОВІДІ", "angry"),
    ("Які способи оплати у вас є?", None),
    ("Ви людина чи бот?", None),
    ("Покличте менеджера", "explicit"),
    ("Передзвоніть мені, будь ласка", "explicit"),
    ("Потрібно 4 камери на приватний будинок", None),
])
def test_handoff_triggers(text, reason):
    assert detect_handoff(text) == reason


def test_price_guard():
    assert unverified_prices("Камера коштує 1525 грн, комплект — 12 160 грн", {1525.0, 12160.0}) == []
    assert unverified_prices("Камера коштує 1499 грн", {1525.0}) == ["1499 грн"]
    assert unverified_prices("Ціну уточнить менеджер", set()) == []


def test_policies_come_from_published_texts():
    assert "14 днів" in policies.policy("returns")["text"]
    assert "Нова пошта" in policies.policy("delivery")["text"] or "Нової пошти" in policies.policy("delivery")["text"]
    assert policies.policy("unknown")["topic"] == "delivery"


class FakeLLM:
    def __init__(self, script):
        self.script, self.calls = list(script), []

    async def chat(self, messages, tools=None):
        self.calls.append(json.loads(json.dumps(messages, ensure_ascii=False)))
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def call(name, args, cid="c1"):
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]}


def run(coro):
    return asyncio.run(coro)


async def no_stock(items):
    return [{"id": i["id"], "stock": "перевірити вручну"} for i in items]


def test_consultant_answers_with_tool_prices_and_cart_link():
    fake = FakeLLM([
        call("build_kit", {"cameras": 4}),
        call("create_cart_link", {"items": [{"id": "viatec-1", "qty": 4}, {"id": "viatec-10", "qty": 1}]}, "c2"),
        {"role": "assistant", "content": "Пропоную 4 камери по 1525 грн і реєстратор 6060 грн. Разом 12160 грн."},
    ])
    result = run(Consultant(fake, product_catalog=CATALOG, stock_checker=no_stock).reply(
        [{"role": "user", "content": "Потрібно 4 камери на будинок"}]))
    assert result.handoff is None and "12160 грн" in result.text
    assert "catalog.html?cart=viatec-1:4,viatec-10:1" in result.text   # appended automatically
    assert fake.calls[0][0]["role"] == "system" and "НЕ людина" in fake.calls[0][0]["content"]
    tool_msgs = [m for m in fake.calls[1] if m["role"] == "tool"]
    assert tool_msgs and "viatec-1" in tool_msgs[0]["content"]


def test_invented_price_is_blocked():
    fake = FakeLLM([call("search_products", {"query": "камера poe"}),
                    {"role": "assistant", "content": "Ця камера коштує 999 грн"}])
    result = run(Consultant(fake, product_catalog=CATALOG).reply([{"role": "user", "content": "скільки камера poe?"}]))
    assert result.text is None and result.handoff == "unverified"


def test_llm_handoff_tool_and_payment_shortcut():
    fake = FakeLLM([call("handoff_to_manager", {"reason": "complex", "summary": "30 камер на склад"}),
                    {"role": "assistant", "content": "Передаю питання менеджеру."}])
    result = run(Consultant(fake, product_catalog=CATALOG).reply([{"role": "user", "content": "Треба 30 камер на склад"}]))
    assert result.handoff == "complex" and result.text == "Передаю питання менеджеру."
    fake = FakeLLM([])
    result = run(Consultant(fake, product_catalog=CATALOG).reply([{"role": "user", "content": "Надішліть рахунок на оплату"}]))
    assert result.handoff == "payment" and fake.calls == []  # no LLM call for payment


def test_llm_unavailable_falls_back_to_handoff():
    fake = FakeLLM([llm.LLMUnavailable("rate_limited")])
    result = run(Consultant(fake, product_catalog=CATALOG).reply([{"role": "user", "content": "Є камери Dahua?"}]))
    assert result.handoff == "ai_unavailable" and result.text is None


def test_stock_tool_never_claims_availability_itself():
    fake = FakeLLM([call("check_stock", {"ids": ["viatec-1"]}),
                    {"role": "assistant", "content": "Наявність підтвердить менеджер."}])
    result = run(Consultant(fake, product_catalog=CATALOG, stock_checker=no_stock).reply([{"role": "user", "content": "є в наявності viatec-1?"}]))
    assert "check_stock" in result.tools_used and "перевірити вручну" in fake.calls[1][-1]["content"]


class FakeResponse:
    def __init__(self, status, payload=None, headers=None):
        self.status, self.payload, self.headers = status, payload, headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self, content_type=None):
        return self.payload

    async def text(self):
        return json.dumps(self.payload)


def fake_session_factory(responses, seen):
    class Session:
        def __init__(self, timeout=None):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        def post(self, url, json=None, headers=None):
            seen.append((url, json, headers))
            return responses.pop(0)
    return Session


def test_llm_client_backoff_on_429(monkeypatch):
    sleeps = []

    async def fast_sleep(delay):
        sleeps.append(delay)
    monkeypatch.setattr(llm.asyncio, "sleep", fast_sleep)
    llm.LLMClient._last_call, llm.LLMClient._count = 0.0, 0
    seen = []
    ok = {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
    client = llm.LLMClient("k", "https://example.test/v1/", "m", min_interval=0,
                           session_factory=fake_session_factory([FakeResponse(429, {}, {"Retry-After": "1"}), FakeResponse(200, ok)], seen))
    assert run(client.chat([{"role": "user", "content": "x"}]))["content"] == "ok"
    assert 1.0 in sleeps and seen[0][0] == "https://example.test/v1/chat/completions"
    assert seen[0][2]["Authorization"] == "Bearer k"
    client = llm.LLMClient("k", "https://example.test/v1", "m", min_interval=0, max_wait=3,
                           session_factory=fake_session_factory([FakeResponse(429, {}) for _ in range(3)], []))
    with pytest.raises(llm.LLMUnavailable) as err:
        run(client.chat([{"role": "user", "content": "x"}]))
    assert err.value.reason == "rate_limited"
    client = llm.LLMClient("k", "https://example.test/v1", "m", min_interval=0,
                           session_factory=fake_session_factory([FakeResponse(400, {"error": "bad"})], []))
    with pytest.raises(llm.LLMUnavailable):
        run(client.chat([{"role": "user", "content": "x"}]))


def test_daily_limit(monkeypatch):
    llm.LLMClient._count, llm.LLMClient._day = 0, None
    client = llm.LLMClient("k", "https://example.test", "m", min_interval=0, daily_limit=1,
                           session_factory=fake_session_factory([FakeResponse(200, {"choices": [{"message": {"content": "a"}}]})], []))
    run(client.chat([]))
    with pytest.raises(llm.LLMUnavailable) as err:
        run(client.chat([]))
    assert err.value.reason == "daily_limit"


def test_ai_disabled_without_key(monkeypatch):
    from bot.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", None)
    assert not settings.ai_active
    monkeypatch.setattr(settings, "llm_api_key", "x")
    assert settings.ai_active


def test_system_prompt_rules():
    prompt = consultant.SYSTEM_PROMPT
    assert "помічник ALT-CAM" in prompt and "НЕ людина" in prompt and "Ніколи не вигадуй ціну" in prompt
    assert "помічник ALT-CAM" in consultant.INTRO and "автоматичний" in consultant.INTRO


def test_unverified_delivery_times_are_removed():
    from bot.ai.consultant import strip_unverified_durations

    text = "Відправляємо Новою поштою. Зазвичай доставка займає 1–2 дні. Протягом 14 днів можна повернути."
    out = strip_unverified_durations(text, "повернення протягом 14 днів")
    assert "1–2 дні" not in out and "14 днів" in out and out.startswith("Відправляємо")
