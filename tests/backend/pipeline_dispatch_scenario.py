"""Real aiogram Dispatcher + routers + middleware with a fake Telegram session (run by test_pipeline_db.py)."""
import asyncio
import os
from datetime import datetime, timezone

os.environ.update(ADMIN_CHAT_ID="111", ADMIN_IDS="111", PIPELINE_LINK_SECRET="x", WORK_HOURS="00:00-23:59", WORK_DAYS="0,1,2,3,4,5,6")

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.methods import CopyMessage, SendMessage  # noqa: E402
from aiogram.types import CallbackQuery, Chat, Message, MessageId, PhotoSize, Update, User  # noqa: E402
from sqlalchemy import select  # noqa: E402

from bot.db.base import SessionLocal, create_db_schema, engine  # noqa: E402
from bot.db.models import Inquiry, InquiryEvent  # noqa: E402
from bot.handlers import admin, auction, client_quiz, group_guide, installer, pipeline_client, pipeline_owner, service, start  # noqa: E402
from bot.middlewares import captcha  # noqa: E402
from bot.middlewares.terms import TermsMiddleware  # noqa: E402

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


def sent(kind=None):
    rows = [(type(c).__name__, getattr(c, "chat_id", None), getattr(c, "text", "") or "") for c in calls]
    calls.clear()
    return [r for r in rows if kind is None or r[0] == kind]


async def main():
    await create_db_schema()
    bot = Bot("123:ABC", session=FakeSession())
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(TermsMiddleware())
    dp.callback_query.middleware(TermsMiddleware())
    for router in (captcha.router, group_guide.router, pipeline_owner.router, pipeline_client.deeplink_router, start.router,
                   client_quiz.router, service.router, installer.router, auction.router, admin.router, pipeline_client.router):
        dp.include_router(router)
    client, chat = User(id=555, is_bot=False, first_name="Клієнт"), Chat(id=555, type="private")
    owner, owner_chat = User(id=111, is_bot=False, first_name="Owner"), Chat(id=111, type="private")
    now = lambda: datetime.now(timezone.utc)  # noqa: E731

    def message(i, user=client, where=chat, **kw):
        return Update(update_id=i, message=Message(message_id=i, date=now(), chat=where, from_user=user, **kw))

    # Site button: instant greeting, no captcha, owner informed
    await dp.feed_update(bot, message(1, text="/start"))
    out = sent()
    assert out[0][1] == 555 and "№1" in out[0][2], out
    assert any(chat_id == 111 for _, chat_id, _ in out)

    # First real question (terms never accepted): captured, card + copy to owner, waiting starts
    await dp.feed_update(bot, message(2, text="Є камера DS-2CD?"))
    out = sent()
    assert ("CopyMessage", 111, "") in out and any(k == "SendMessage" and c == 111 for k, c, _ in out), out
    async with SessionLocal() as s:
        assert (await s.get(Inquiry, 1)).awaiting_since is not None

    # Photo without text is captured too
    await dp.feed_update(bot, message(3, photo=[PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]))
    assert ("CopyMessage", 111, "") in sent()

    # A returning customer stays in the same consultation, not the legacy menu.
    await dp.feed_update(bot, message(4, text="/start"))
    assert "№1" in sent()[0][2]
    # Explicit questionnaire intent still uses the existing captcha flow.
    await dp.feed_update(bot, message(40, text="/start client"))
    assert "відеокамеру" in sent()[0][2]
    await dp.feed_update(bot, message(5, text="ще питання"))
    assert ("CopyMessage", 111, "") in sent()

    # FAQ works even inside captcha state
    cq = CallbackQuery(id="c1", from_user=client, chat_instance="x", data="faq:dlv",
                       message=Message(message_id=9, date=now(), chat=chat, text="x"))
    await dp.feed_update(bot, Update(update_id=6, callback_query=cq))
    assert "Доставка" in sent("SendMessage")[0][2]

    # Owner: one tap 'take' notifies the client; swipe-reply is relayed to the client
    cq = CallbackQuery(id="c2", from_user=owner, chat_instance="x", data="inq:1:take",
                       message=Message(message_id=10, date=now(), chat=owner_chat, text="card"))
    await dp.feed_update(bot, Update(update_id=7, callback_query=cq))
    assert any(c == 555 and "взято в роботу" in t for _, c, t in sent("SendMessage"))
    async with SessionLocal() as s:
        copied_id = await s.scalar(select(InquiryEvent.owner_message_id).where(InquiryEvent.kind == "owner_copy").limit(1))
    reply_to = Message(message_id=copied_id, date=now(), chat=owner_chat, text="copy")
    await dp.feed_update(bot, message(20, user=owner, where=owner_chat, text="Так, є в наявності", reply_to_message=reply_to))
    assert ("CopyMessage", 555, "") in sent()

    # A non-owner cannot press owner buttons
    cq = CallbackQuery(id="c3", from_user=client, chat_instance="x", data="inq:1:st:rejected",
                       message=Message(message_id=11, date=now(), chat=chat, text="card"))
    await dp.feed_update(bot, Update(update_id=8, callback_query=cq))
    sent()
    async with SessionLocal() as s:
        assert (await s.get(Inquiry, 1)).status == "taken"

    # /sla dashboard
    await dp.feed_update(bot, message(21, user=owner, where=owner_chat, text="/sla"))
    assert "SLA" in sent("SendMessage")[0][2]
    await engine.dispose()
    print("PIPELINE_DISPATCH_SCENARIO_OK")


asyncio.run(main())
