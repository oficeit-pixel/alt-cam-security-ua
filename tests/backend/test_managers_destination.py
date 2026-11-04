from types import SimpleNamespace
from unittest.mock import patch
from bot.pipeline.notify import escalation_targets


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
