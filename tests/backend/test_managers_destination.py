from types import SimpleNamespace
from unittest.mock import patch
from bot.pipeline.notify import escalation_targets
from unittest.mock import AsyncMock
import pytest
from bot.handlers.pipeline_client import _copy_to_owner


def test_managers_receive_initial_card_without_waiting_for_escalation():
    settings = SimpleNamespace(managers_chat_id=-100123, owner_chat_id=123,
                               second_contact_target=456, site_lead_group_id=-100123)
    with patch("bot.pipeline.notify.get_settings", return_value=settings):
        assert escalation_targets(1) == [-100123, 123]
        assert escalation_targets(3) == [-100123, 123, 456]


def test_unconfigured_managers_does_not_change_existing_routes():
    settings = SimpleNamespace(managers_chat_id=None, owner_chat_id=123,
                               second_contact_target=None, site_lead_group_id=None)
    with patch("bot.pipeline.notify.get_settings", return_value=settings):
        assert escalation_targets(1) == [123]


@pytest.mark.asyncio
async def test_client_messages_reach_group_and_owner_even_if_one_copy_fails():
    message = SimpleNamespace(bot=SimpleNamespace(copy_message=AsyncMock(
        side_effect=[RuntimeError("unavailable"), SimpleNamespace(message_id=9)])),
        chat=SimpleNamespace(id=777), message_id=8)
    with patch("bot.pipeline.notify.escalation_targets", return_value=[-100123, 123]), \
         patch("bot.pipeline.notify.send_owner_card", new_callable=AsyncMock) as cards, \
         patch("bot.pipeline.service.add_event", new_callable=AsyncMock) as events:
        await _copy_to_owner(message, AsyncMock(), SimpleNamespace(id=1), "New", force_card=True)
    assert cards.await_count == 2
    assert message.bot.copy_message.await_count == 2
    events.assert_awaited_once()
