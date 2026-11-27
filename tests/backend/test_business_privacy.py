"""Personal chats are opt-in; disabling Business must stop ingress and egress."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.config import get_settings
from bot.handlers import pipeline_business
from bot.pipeline import delivery, jobs
from bot.ai import runtime


@pytest.fixture
def disabled(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "business_enabled", False)
    return settings


def test_no_personal_message_or_connection_reads_database(disabled, monkeypatch):
    def forbidden():
        raise AssertionError("Personal chat must not reach storage")
    monkeypatch.setattr(pipeline_business, "SessionLocal", forbidden)
    assert asyncio.run(pipeline_business.handle_business_message(SimpleNamespace())) == "ignored"
    asyncio.run(pipeline_business.on_business_connection(SimpleNamespace()))


@pytest.mark.parametrize("connection,source", [("personal", "telegram_business"), (None, "telegram_business"), ("personal", "telegram")])
def test_old_business_inquiry_cannot_send(disabled, connection, source):
    bot = SimpleNamespace(send_message=AsyncMock())
    inquiry = SimpleNamespace(client_chat_id=123, business_connection_id=connection, source=source)
    assert delivery.business_blocked(inquiry)
    assert not asyncio.run(delivery.send_client_text(bot, inquiry, "private"))
    bot.send_message.assert_not_called()


def test_client_bot_still_sends(disabled):
    bot = SimpleNamespace(send_message=AsyncMock())
    inquiry = SimpleNamespace(client_chat_id=123, business_connection_id=None, source="telegram")
    assert asyncio.run(delivery.send_client_text(bot, inquiry, "client reply"))
    bot.send_message.assert_awaited_once()


def test_business_ai_disabled_before_storage(disabled, monkeypatch):
    monkeypatch.setattr(disabled, "ai_business_enabled", True)
    assert asyncio.run(runtime.respond(None, None, None, business=True)) == "disabled"


@pytest.mark.parametrize("job", ["run_reminders", "run_followups", "run_np_tracking"])
def test_background_jobs_ignore_old_personal_inquiries(disabled, monkeypatch, job):
    inquiry = SimpleNamespace(business_connection_id="personal", source="telegram_business")
    class Session:
        commit = AsyncMock()
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(jobs, "SessionLocal", Session)
    monkeypatch.setattr(jobs.schedule, "is_working_time", lambda now: True)
    monkeypatch.setattr(jobs.contacts, "safe_reload", AsyncMock())
    monkeypatch.setattr(jobs.service, "repair_stale_sla", AsyncMock(return_value=0))
    monkeypatch.setattr(jobs.service, "due_reminders", AsyncMock(return_value=[(inquiry, 1)]))
    monkeypatch.setattr(jobs.service, "due_followups", AsyncMock(return_value=[inquiry]))
    monkeypatch.setattr(jobs.service, "shipped_with_ttn", AsyncMock(return_value=[inquiry]))
    monkeypatch.setattr(disabled, "nova_poshta_api_key", "test-only")
    claim = AsyncMock(side_effect=AssertionError("Must not claim a personal inquiry"))
    monkeypatch.setattr(jobs.service, "claim_reminder", claim)
    monkeypatch.setattr(jobs.service, "claim_followup", claim)
    monkeypatch.setattr(jobs.np, "fetch_statuses", claim)
    assert asyncio.run(getattr(jobs, job)(SimpleNamespace())) == 0
