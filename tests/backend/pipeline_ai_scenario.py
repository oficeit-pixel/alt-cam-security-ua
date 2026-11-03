"""AI consultant inside the real pipeline (Dispatcher + DB + fake Telegram + fake LLM). Run by test_pipeline_db.py."""
import asyncio
import json
import os
from datetime import datetime, timezone

os.environ.update(ADMIN_CHAT_ID="111", ADMIN_IDS="111", SECOND_CONTACT_CHAT_ID="222", PIPELINE_LINK_SECRET="x",
                  WORK_HOURS="00:00-23:59", WORK_DAYS="0,1,2,3,4,5,6", LLM_API_KEY="fake-key", AI_MIN_INTERVAL_SECONDS="0")

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.methods import CopyMessage, SendMessage  # noqa: E402
from aiogram.types import BusinessBotRights, BusinessConnection, CallbackQuery, Chat, Message, MessageId, Update, User  # noqa: E402
from sqlalchemy import select  # noqa: E402

from bot.ai import runtime  # noqa: E402
from bot.ai.consultant import BUSINESS_PREFIX, Consultant  # noqa: E402
from bot.ai.llm import LLMUnavailable  # noqa: E402
from bot.db.base import SessionLocal, create_db_schema, engine  # noqa: E402
from bot.db.models import AIChatPref, Inquiry, InquiryEvent  # noqa: E402
from bot.handlers import (admin, auction, client_quiz, group_guide, installer, pipeline_business,  # noqa: E402
                          pipeline_client, pipeline_owner, service, start)
from bot.middlewares import captcha  # noqa: E402
from bot.middlewares.terms import TermsMiddleware  # noqa: E402

calls = []
script = []


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        calls.append(method)
        if isinstance(method, SendMessage):
            return Message(message_id=len(calls) + 100, date=datetime.now(timezone.utc),
                           chat=Chat(id=method.chat_id, type="private"), text=method.text)
        if isinstance(method, CopyMessage):
            return MessageId(message_id=len(calls) + 100)
        return True

    async def stream_content(self, *args, **kwargs):
        yield b""

    async def close(self):
        pass


class ScriptedLLM:
    async def chat(self, messages, tools=None):
        step = script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


async def factory(session):
    return Consultant(ScriptedLLM(), overrides=await runtime._overrides(session))


def sent():
    rows = [m for m in calls if isinstance(m, SendMessage)]
    calls.clear()
    return rows


def tool(name, args):
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": "t1", "type": "function", "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]}


async def main():
    await create_db_schema()
    runtime.set_consultant_factory(factory)
    bot = Bot("123:ABC", session=FakeSession())
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(TermsMiddleware())
    dp.callback_query.middleware(TermsMiddleware())
    for router in (captcha.router, group_guide.router, pipeline_owner.router, pipeline_business.router,
                   pipeline_client.deeplink_router, start.router, client_quiz.router, service.router, installer.router,
                   auction.router, admin.router, pipeline_client.router):
        dp.include_router(router)
    now = lambda: datetime.now(timezone.utc)  # noqa: E731
    seq = iter(range(1, 1000))
    client = User(id=555, is_bot=False, first_name="Клієнт")
    owner = User(id=111, is_bot=False, first_name="Owner", username="OficeITHelp")

    def msg(user, text, chat_id=None, **kw):
        return Message(message_id=next(seq), date=now(), chat=Chat(id=chat_id or user.id, type="private"),
                       from_user=user, text=text, **kw)

    async def feed(**kw):
        await dp.feed_update(bot, Update(update_id=next(seq), **kw))

    # 1. Bot chat: AI answers with intro + real catalog search, no standard auto-reply, waiting cleared
    script[:] = [tool("search_products", {"query": "відеокамера poe"}),
                 {"role": "assistant", "content": "Можу запропонувати IP-камери з PoE — підкажіть, вулиця чи приміщення?"}]
    await feed(message=msg(client, "Підкажіть камеру для будинку"))
    out = sent()
    to_client = [m for m in out if m.chat_id == 555]
    assert len(to_client) == 1 and "помічник ALT-CAM" in to_client[0].text and to_client[0].reply_markup is not None, to_client
    assert not any("отримано ✅" in m.text for m in to_client)
    assert any(m.chat_id == 111 and "AI відповів" in m.text for m in out)
    async with SessionLocal() as s:
        inquiry = await s.scalar(select(Inquiry).where(Inquiry.client_tg_id == 555))
        assert inquiry.awaiting_since is None
        kinds = [e.kind for e in (await s.scalars(select(InquiryEvent).where(InquiryEvent.inquiry_id == inquiry.id))).all()]
        assert "ai_reply" in kinds
        inquiry_id = inquiry.id

    # 2. Second answer: no repeated intro; history includes previous turns
    script[:] = [{"role": "assistant", "content": "Для вулиці підійдуть циліндричні IP-камери."}]
    await feed(message=msg(client, "На вулицю"))
    reply = [m for m in sent() if m.chat_id == 555][0]
    assert "помічник ALT-CAM" not in reply.text and "циліндричні" in reply.text

    # 3. Payment -> hand-off without LLM: client informed, owner + partner alerted, AI paused, waiting restarted
    script[:] = []
    await feed(message=msg(client, "Ок, надішліть реквізити для оплати"))
    out = sent()
    assert any(m.chat_id == 555 and "Передаю ваше питання менеджеру" in m.text for m in out)
    alerts = [m for m in out if "AI передає розмову" in (m.text or "")]
    assert {m.chat_id for m in alerts} == {111, 222}, out
    async with SessionLocal() as s:
        assert (await s.get(AIChatPref, 555)).paused
        assert (await s.get(Inquiry, inquiry_id)).awaiting_since is not None

    # 4. Paused: next message is not answered by AI (script empty would raise if called)
    await feed(message=msg(client, "Чекаю"))
    assert not any(m.chat_id == 555 for m in sent())

    # 5. Owner resumes AI with /ai_on <id>
    await feed(message=msg(owner, f"/ai_on {inquiry_id}"))
    assert "увімкнено" in sent()[0].text
    async with SessionLocal() as s:
        assert not (await s.get(AIChatPref, 555)).paused
    # card button toggles it off again
    cq = CallbackQuery(id="c1", from_user=owner, chat_instance="x", data=f"inq:{inquiry_id}:ai",
                       message=Message(message_id=900, date=now(), chat=Chat(id=111, type="private"), text="card"))
    await feed(callback_query=cq)
    sent()
    async with SessionLocal() as s:
        assert (await s.get(AIChatPref, 555)).paused

    # 6. LLM down (429 after retries) -> standard auto-reply for a new client + owner alert, never silence
    other = User(id=556, is_bot=False, first_name="K2")
    script[:] = [LLMUnavailable("rate_limited")]
    await feed(message=msg(other, "Є домофони?"))
    out = sent()
    assert any(m.chat_id == 556 and "отримано ✅" in m.text for m in out), out
    assert any(m.chat_id == 111 and "AI недоступний" in m.text for m in out)
    async with SessionLocal() as s:
        assert await s.get(AIChatPref, 556) is None  # temporary outage does not pause AI
    script[:] = [LLMUnavailable("rate_limited")]
    await feed(message=msg(other, "Алло?"))
    assert any(m.chat_id == 556 and "Передаю ваше питання менеджеру" in m.text for m in sent())

    # 7. Telegram Business chat: AI answers as the assistant (prefixed), no first-person ack
    await feed(business_connection=BusinessConnection(id="bc1", user=owner, user_chat_id=111, date=now(),
                                                      rights=BusinessBotRights(can_reply=True), is_enabled=True))
    sent()
    biz = User(id=777, is_bot=False, first_name="B")
    script[:] = [{"role": "assistant", "content": "Підкажіть, скільки камер потрібно?"}]
    await feed(business_message=msg(biz, "Хочу відеонагляд у магазин", business_connection_id="bc1"))
    out = [m for m in sent() if m.chat_id == 777]
    assert len(out) == 1 and out[0].text.startswith(BUSINESS_PREFIX) and out[0].business_connection_id == "bc1"
    assert "Отримав" not in out[0].text
    # owner answers himself -> AI pauses in that chat
    await feed(business_message=msg(owner, "Добрий день! Скільки камер?", chat_id=777, business_connection_id="bc1"))
    async with SessionLocal() as s:
        assert (await s.get(AIChatPref, 777)).paused
    script[:] = []
    await feed(business_message=msg(biz, "4 камери", business_connection_id="bc1"))
    assert not any(m.chat_id == 777 for m in sent())

    await engine.dispose()
    print("PIPELINE_AI_SCENARIO_OK")


asyncio.run(main())
