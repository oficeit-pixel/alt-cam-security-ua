"""Executed in a subprocess by test_pipeline_db.py with DATABASE_URL -> disposable local DB."""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

os.environ.setdefault("PIPELINE_LINK_SECRET", "db-test-secret")
os.environ.update(ADMIN_CHAT_ID="111", ADMIN_IDS="111", SECOND_CONTACT_CHAT_ID="222", SITE_LEAD_GROUP_ID="-333",
                  BOT_USERNAME="AltCamSecurityUaBot")

from sqlalchemy import func, select  # noqa: E402

from bot.db.base import SessionLocal, create_db_schema, engine  # noqa: E402
from bot.db.models import Inquiry, InquiryEvent, SiteLead, WebOrder  # noqa: E402
from bot.handlers import pipeline_client, pipeline_owner  # noqa: E402
from bot.pipeline import capture, jobs, links, service  # noqa: E402

KYIV = timezone(timedelta(hours=2))
WORK_NOW = datetime(2026, 11, 3, 10, 0, tzinfo=KYIV)  # Tuesday 10:00 Kyiv


class FakeBot:
    def __init__(self):
        self.sent, self.copied, self._id = [], [], 1000

    async def send_message(self, chat_id, text, **kw):
        self._id += 1
        self.sent.append((chat_id, text, kw.get("reply_markup")))
        return SimpleNamespace(message_id=self._id)

    async def copy_message(self, chat_id, from_chat_id, message_id, **kw):
        self._id += 1
        self.copied.append((chat_id, from_chat_id, message_id))
        return SimpleNamespace(message_id=self._id)


def client_message(bot, text, user_id=555, message_id=1):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id, username="client", full_name="Клієнт Тест"),
        chat=SimpleNamespace(id=user_id, type="private"), message_id=message_id, text=text, caption=None,
        photo=None, document=None, contact=None, location=None, bot=bot, answer=AsyncMock(),
    )


def owner_callback(bot, data, chat_id=111):
    message = SimpleNamespace(chat=SimpleNamespace(id=chat_id), edit_text=AsyncMock(), answer=AsyncMock())
    return SimpleNamespace(data=data, from_user=SimpleNamespace(id=111), message=message, bot=bot, answer=AsyncMock())


class FakeState:
    def __init__(self):
        self.state, self.data = None, {}

    async def set_state(self, value):
        self.state = value

    async def update_data(self, **kw):
        self.data.update(kw)

    async def get_data(self):
        return dict(self.data)

    async def clear(self):
        self.state, self.data = None, {}


async def main():
    await create_db_schema()
    await create_db_schema()  # idempotent
    bot = FakeBot()

    # 1) Bot chat: capture + instant auto-reply + owner card & copy; repeat message appends, no 2nd auto-reply
    msg = client_message(bot, "Є Hikvision DS-2CD1043G2-I?")
    inquiry = await pipeline_client.capture_client_message(msg)
    assert msg.answer.await_count == 1 and "№" in msg.answer.await_args.args[0]
    assert any(chat == 111 for chat, *_ in bot.sent) and bot.copied[0][0] == 111
    msg2 = client_message(bot, "І ще блок живлення", message_id=2)
    again = await pipeline_client.capture_client_message(msg2)
    assert again.id == inquiry.id and msg2.answer.await_count == 0

    # 2) Escalation: nothing before 5 min, then levels 1/2/3 with widening targets, never duplicated
    async with SessionLocal() as s:
        row = await s.get(Inquiry, inquiry.id)
        row.awaiting_since = WORK_NOW - timedelta(minutes=4)
        await s.commit()
    bot.sent.clear()
    assert await jobs.run_reminders(bot, WORK_NOW) == 0
    for minutes, expected_targets in ((5, {111}), (15, {111, 222}), (60, {111, 222, -333})):
        bot.sent.clear()
        now = WORK_NOW - timedelta(minutes=4) + timedelta(minutes=minutes)
        await jobs.run_reminders(bot, now)
        assert {chat for chat, *_ in bot.sent} == expected_targets, (minutes, bot.sent)
        bot.sent.clear()
        await jobs.run_reminders(bot, now)
        assert bot.sent == [], "reminder must not repeat"
    night = datetime(2026, 11, 3, 23, 0, tzinfo=KYIV)
    assert await jobs.run_reminders(bot, night) == 0

    # 3) Owner one-tap: take -> client notified, waiting cleared; template 'yes' -> stock_checked
    state = FakeState()
    bot.sent.clear()
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:take"), state)
    async with SessionLocal() as s:
        row = await s.get(Inquiry, inquiry.id)
        assert row.status == "taken" and row.awaiting_since is None and row.first_response_at is not None
    assert any(chat == 555 for chat, *_ in bot.sent)
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:tpl:yes"), state)
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:tpl:cnf"), state)
    async with SessionLocal() as s:
        row = await s.get(Inquiry, inquiry.id)
        assert row.status == "offer_sent", row.status

    # 4) 24h silence -> one follow-up with confirm buttons; client confirms -> confirmed
    later = WORK_NOW + timedelta(hours=25)
    async with SessionLocal() as s:
        row = await s.get(Inquiry, inquiry.id)
        row.last_owner_msg_at = WORK_NOW
        row.last_client_msg_at = WORK_NOW - timedelta(minutes=30)
        await s.commit()
    bot.sent.clear()
    assert await jobs.run_followups(bot, later) == 1
    assert await jobs.run_followups(bot, later) == 0
    cb = SimpleNamespace(data=f"cli:{inquiry.id}:ok", from_user=SimpleNamespace(id=555), bot=bot,
                         message=SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=555, type="private")), answer=AsyncMock())
    await pipeline_client.client_decision(cb)
    foreign = SimpleNamespace(data=f"cli:{inquiry.id}:no", from_user=SimpleNamespace(id=999), bot=bot,
                              message=SimpleNamespace(answer=AsyncMock(), chat=SimpleNamespace(id=999, type="private")), answer=AsyncMock())
    await pipeline_client.client_decision(foreign)
    async with SessionLocal() as s:
        row = await s.get(Inquiry, inquiry.id)
        assert row.status == "confirmed", row.status

    # 5) Payment COD -> TTN -> shipped; client gets TTN
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:pm:cod"), state)
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:st:supplier_ordered"), state)
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:st:supplier_paid"), state)
    await pipeline_owner.owner_action(owner_callback(bot, f"inq:{inquiry.id}:ttn"), state)
    assert state.data["inquiry_id"] == inquiry.id
    bot.sent.clear()
    ttn_msg = SimpleNamespace(text="20450000000000", from_user=SimpleNamespace(id=111), chat=SimpleNamespace(id=111),
                              bot=bot, answer=AsyncMock())
    await pipeline_owner.owner_ttn(ttn_msg, state)
    async with SessionLocal() as s:
        row = await s.get(Inquiry, inquiry.id)
        assert row.status == "shipped" and row.ttn == "20450000000000" and row.payment_method == "cod"
    assert any(chat == 555 and "20450000000000" in text for chat, text, _ in bot.sent)

    # 6) Invalid transition is rejected with an alert, status unchanged
    bad = owner_callback(bot, f"inq:{inquiry.id}:st:new")
    await pipeline_owner.owner_action(bad, state)
    assert bad.answer.await_args.kwargs.get("show_alert") is True

    # 7) Site order -> inquiry + signed deep link; binding via /start o<id>_sig; status sync to web order
    async with SessionLocal() as s:
        order = WebOrder(order_number="WEB-20261103-ABCDEF", customer={"name": "Марія", "phone": "+380500000000"},
                         delivery={"label": "НП 1"}, items=[{"id": "viatec-2", "name": "Cam", "price": 1, "quantity": 1}],
                         subtotal=1, status="new")
        s.add(order)
        await s.commit()
        await s.refresh(order)
    link = await capture.capture_site_order(bot, order)
    assert link and link.startswith("https://t.me/AltCamSecurityUaBot?start=o")
    param = link.split("start=")[1]
    start_msg = client_message(bot, f"/start {param}", user_id=777)
    await pipeline_client.start_deeplink(start_msg, SimpleNamespace(args=param))
    async with SessionLocal() as s:
        site_inq = await service.inquiry_for_web_order(s, order.id)
        assert site_inq.client_tg_id == 777 and site_inq.source == "site_order"
        await service.transition(s, site_inq, "supplier_ordered", actor="test")
        await s.commit()
        assert (await s.get(WebOrder, order.id)).status == "ordered_from_supplier"

    # 8) Site lead -> inquiry; reminder for lead without Telegram contains the phone
    async with SessionLocal() as s:
        lead = SiteLead(type="Консультація", name="Олег", phone="+380671112233", email="", message="Потрібні камери",
                        payload={}, page="/")
        s.add(lead)
        await s.commit()
        await s.refresh(lead)
    assert await capture.capture_site_lead(bot, lead.id, {"type": "Консультація", "client": {"name": "Олег", "phone": "+380671112233"}, "message": "Потрібні камери"})
    async with SessionLocal() as s:
        lead_inq = await service.inquiry_for_site_lead(s, lead.id)
        lead_inq.awaiting_since = WORK_NOW - timedelta(minutes=6)
        await s.commit()
    bot.sent.clear()
    await jobs.run_reminders(bot, WORK_NOW)
    assert any("+380671112233" in text for _, text, _ in bot.sent)

    # 9) SLA summary + owner message mapping for swipe-replies
    async with SessionLocal() as s:
        items = await service.open_inquiries(s)
        summary = service.sla_summary(items, WORK_NOW)
        assert summary["open"] >= 2 and summary["waiting"] >= 1
        event = await s.scalar(select(InquiryEvent).where(InquiryEvent.owner_message_id.is_not(None)).limit(1))
        assert (await service.inquiry_by_owner_message(s, event.owner_chat_id, event.owner_message_id)) is not None
        assert await s.scalar(select(func.count()).select_from(InquiryEvent)) > 10
    # 10) Status acknowledgement ends old SLA; a fresh client question restarts it.
    async with SessionLocal() as s:
        row = await service.create_inquiry(s, source="test", now=WORK_NOW - timedelta(minutes=507))
        await service.transition(s, row, "offer_sent", actor="owner", now=WORK_NOW)
        assert row.awaiting_since is None and row.reminder_level == 0
        assert row.last_owner_msg_at is None  # don't fabricate a message that was never sent
        # Reproduce legacy data, then repair it exactly once with an audit event.
        row.awaiting_since = WORK_NOW - timedelta(minutes=507)
        row.reminder_level = 3
        await s.commit()
        assert await service.repair_stale_sla(s) == 1
        await s.commit()
        await s.refresh(row)
        assert row.awaiting_since is None and row.reminder_level == 0
        assert await service.repair_stale_sla(s) == 0
        later_question = WORK_NOW + timedelta(minutes=1)
        await service.record_client_message(s, row, "New question", now=later_question)
        await s.commit()
        assert await service.repair_stale_sla(s) == 0
        due = await service.due_reminders(s, [5, 15, 60], later_question + timedelta(minutes=5))
        assert any(i.id == row.id and level == 1 for i, level in due)
        assert row.awaiting_since == later_question
    await engine.dispose()
    print("PIPELINE_DB_SCENARIO_OK")


asyncio.run(main())
