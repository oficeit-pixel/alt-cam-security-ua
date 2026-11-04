"""Auto-registration of owner/second contact + Telegram Business flow (real Dispatcher, fake Telegram session).

Run by test_pipeline_db.py against a disposable local PostgreSQL. No ADMIN_* ids configured on purpose.
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone

for _name in ("ADMIN_CHAT_ID", "ADMIN_IDS", "SECOND_CONTACT_CHAT_ID", "NOVA_POSHTA_API_KEY"):
    os.environ.pop(_name, None)
os.environ.update(PIPELINE_LINK_SECRET="x",
                  WORK_HOURS="00:00-23:59", WORK_DAYS="0,1,2,3,4,5,6",
                  PIPELINE_SCHEDULER_ENABLED="true")

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.methods import CopyMessage, SendMessage  # noqa: E402
from aiogram.types import BusinessBotRights, BusinessConnection, CallbackQuery, Chat, Message, MessageId, Update, User  # noqa: E402
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # noqa: E402
from sqlalchemy import select, update  # noqa: E402

from bot.config import get_settings  # noqa: E402
from bot.db.base import SessionLocal, create_db_schema, engine  # noqa: E402
from bot.db.models import BusinessConnectionRecord, Inquiry, PipelineContact  # noqa: E402
from bot.handlers import (admin, auction, client_quiz, group_guide, installer, pipeline_business,  # noqa: E402
                          pipeline_client, pipeline_owner, service, start)
from bot.handlers.admin import is_admin  # noqa: E402
from bot.middlewares import captcha  # noqa: E402
from bot.middlewares.terms import TermsMiddleware  # noqa: E402
from bot.pipeline import contacts, jobs, texts  # noqa: E402

calls = []


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


def sent():
    rows = [m for m in calls if isinstance(m, SendMessage)]
    calls.clear()
    return rows


async def main():
    await create_db_schema()
    contacts.set_cache({})
    settings = get_settings()
    assert settings.owner_chat_id is None and settings.second_contact_target is None
    bot = Bot("123:ABC", session=FakeSession())
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(TermsMiddleware())
    dp.callback_query.middleware(TermsMiddleware())
    for router in (captcha.router, group_guide.router, pipeline_owner.router, pipeline_business.router,
                   pipeline_client.deeplink_router, start.router, client_quiz.router, service.router, installer.router,
                   auction.router, admin.router, pipeline_client.router):
        dp.include_router(router)
    assert {"business_connection", "business_message"} <= set(dp.resolve_used_update_types())
    now = lambda: datetime.now(timezone.utc)  # noqa: E731
    owner = User(id=111, is_bot=False, first_name="Сергій", username="OficeITHelp")
    partner = User(id=222, is_bot=False, first_name="Partner", username="uniwar")
    stranger = User(id=333, is_bot=False, first_name="X", username="someone")
    client = User(id=555, is_bot=False, first_name="Клієнт", username="client555")
    seq = iter(range(1, 1000))

    def msg(user, text, chat_id=None, **kw):
        return Message(message_id=next(seq), date=now(), chat=Chat(id=chat_id or user.id, type="private"),
                       from_user=user, text=text, **kw)

    async def feed(**kw):
        await dp.feed_update(bot, Update(update_id=next(seq), **kw))

    # 1. Owner and partner press /start -> chat ids stored, reply explains the role
    await feed(message=msg(owner, "/start"))
    out = sent()
    assert out[0].chat_id == 111 and "власник" in out[0].text and "111" in out[0].text, out
    await feed(message=msg(partner, "/start"))
    assert "другий контакт" in sent()[0].text
    assert settings.owner_chat_id == 111 and settings.second_contact_target == 222 and is_admin(111) and is_admin(222)
    async with SessionLocal() as s:
        assert {r.role: r.chat_id for r in (await s.scalars(select(PipelineContact))).all()} == {"owner": 111, "second": 222}
    # repeated /start by the owner -> usual menu, registration unchanged; a stranger is not registered
    await feed(message=msg(owner, "/start"))
    sent()
    await feed(message=msg(stranger, "/start"))
    assert "власник" not in sent()[0].text and not is_admin(333)
    contacts.set_cache({})
    async with SessionLocal() as s:  # survives restart (loaded from DB)
        await contacts.load(s)
    assert settings.owner_chat_id == 111

    # 2. Business connections: owner's accepted, stranger's ignored
    # Bot API 9.0 shape: rights.can_reply (aiogram >= 3.20)
    await feed(business_connection=BusinessConnection(id="bc1", user=owner, user_chat_id=111, date=now(),
                                                      rights=BusinessBotRights(can_reply=True), is_enabled=True))
    assert sent()[0].chat_id == 111
    await feed(business_connection=BusinessConnection(id="bc2", user=stranger, user_chat_id=333, date=now(),
                                                      rights=BusinessBotRights(can_reply=True), is_enabled=True))
    # raw Telegram payload (what polling actually delivers) parses with the pinned aiogram
    raw = {"update_id": 999, "business_connection": {"id": "bc3", "user": {"id": 444, "is_bot": False, "first_name": "Z"},
           "user_chat_id": 444, "date": 1762200000, "is_enabled": True, "rights": {"can_reply": True}}}
    assert Update.model_validate(raw, context={"bot": bot}).business_connection.rights.can_reply
    assert sent() == []
    async with SessionLocal() as s:
        assert (await s.get(BusinessConnectionRecord, "bc1")).allowed
        assert not (await s.get(BusinessConnectionRecord, "bc2")).allowed

    # 3. Client writes to the owner's personal account -> inquiry, one acknowledgement as the owner, owner card
    await feed(business_message=msg(client, "Добрий день, є Hikvision DS-2CD1043?", business_connection_id="bc1"))
    out = sent()
    ack = [m for m in out if m.chat_id == 555]
    assert len(ack) == 1 and ack[0].business_connection_id == "bc1" and ack[0].reply_markup is None
    assert ack[0].text == "Отримав, відповім протягом 5–10 хвилин.", ack[0].text
    assert any(m.chat_id == 111 and "особистому Telegram" in m.text for m in out)
    async with SessionLocal() as s:
        inquiry = await s.scalar(select(Inquiry).where(Inquiry.client_tg_id == 555))
        assert inquiry.source == "telegram_business" and inquiry.business_connection_id == "bc1"
        assert inquiry.awaiting_since is not None and inquiry.status == "new"
        inquiry_id = inquiry.id
    await feed(business_message=msg(client, "і ще реєстратор", business_connection_id="bc1"))
    assert sent() == []  # no second ack, no card spam while waiting

    # our own acknowledgement echoed back / foreign connection -> ignored
    echo = msg(owner, "Отримав", chat_id=555, business_connection_id="bc1", sender_business_bot=User(id=123, is_bot=True, first_name="b"))
    assert await pipeline_business.handle_business_message(echo.as_(bot)) == "ignored"
    other = msg(User(id=777, is_bot=False, first_name="Y"), "hi", business_connection_id="bc2")
    assert await pipeline_business.handle_business_message(other.as_(bot)) == "ignored"

    # 4. Escalation reaches the auto-registered second contact (level 2 after 15 min)
    async with SessionLocal() as s:
        await s.execute(update(Inquiry).where(Inquiry.id == inquiry_id).values(awaiting_since=now() - timedelta(minutes=16)))
        await s.commit()
    assert await jobs.run_reminders(bot) >= 2
    targets = {m.chat_id for m in sent()}
    assert {111, 222} <= targets, targets

    # 5. Owner answers himself in the personal chat -> taken, reminders stop
    await feed(business_message=msg(owner, "Так, є. Куди відправити?", chat_id=555, business_connection_id="bc1"))
    async with SessionLocal() as s:
        inquiry = await s.get(Inquiry, inquiry_id)
        assert inquiry.status == "taken" and inquiry.awaiting_since is None and inquiry.first_response_at is not None
    assert sent() == []

    # 6. Template from the owner card goes to the business chat as plain text (no bot buttons)
    cq = CallbackQuery(id="c1", from_user=owner, chat_instance="x", data=f"inq:{inquiry_id}:tpl:cnf",
                       message=Message(message_id=900, date=now(), chat=Chat(id=111, type="private"), text="card"))
    await feed(callback_query=cq)
    out = [m for m in sent() if m.chat_id == 555]
    assert out and out[0].business_connection_id == "bc1" and out[0].text == texts.BUSINESS_CONFIRM_TEXT

    # 7. Acknowledgement can be disabled
    settings.business_autoreply_enabled = False
    await feed(business_message=msg(User(id=556, is_bot=False, first_name="K2"), "Ціна?", business_connection_id="bc1"))
    out = sent()
    assert not any(m.chat_id == 556 for m in out) and any(m.chat_id == 111 for m in out)
    settings.business_autoreply_enabled = True

    # 8. Without NOVA_POSHTA_API_KEY the tracking job is not scheduled, others are
    scheduler = AsyncIOScheduler()
    assert jobs.setup_pipeline_jobs(scheduler, bot)
    ids = {job.id for job in scheduler.get_jobs()}
    assert "pipeline_reminders" in ids and "pipeline_np_tracking" not in ids, ids
    assert await jobs.run_np_tracking(bot) == 0

    await engine.dispose()
    print("PIPELINE_BUSINESS_SCENARIO_OK")


asyncio.run(main())
