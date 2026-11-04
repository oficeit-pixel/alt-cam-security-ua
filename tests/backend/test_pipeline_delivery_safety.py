from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from bot.handlers.pipeline_client import safe_ack
from bot.pipeline.service import bind_client

@pytest.mark.asyncio
async def test_ack_failure_is_nonfatal():
    message = SimpleNamespace(answer=AsyncMock(side_effect=TelegramForbiddenError(
        method=SendMessage(chat_id=1, text="test"), message="blocked")))
    assert await safe_ack(message, "test") is False

@pytest.mark.asyncio
async def test_ack_success():
    assert await safe_ack(SimpleNamespace(answer=AsyncMock()), "test") is True

def test_signed_link_cannot_replace_bound_client():
    inquiry = SimpleNamespace(client_tg_id=123, client_chat_id=123)
    with pytest.raises(ValueError, match="inquiry_already_bound"):
        bind_client(inquiry, tg_id=456, chat_id=456, username="other", full_name="Other")
    assert inquiry.client_tg_id == 123

def test_same_client_can_reuse_link():
    inquiry = SimpleNamespace(client_tg_id=123, client_chat_id=123, client_name="Name", client_username=None)
    bind_client(inquiry, tg_id=123, chat_id=123, username="same", full_name="Name")
    assert inquiry.client_username == "same"
