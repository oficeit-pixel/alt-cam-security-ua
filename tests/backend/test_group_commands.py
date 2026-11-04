from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.filters import CommandObject
from aiogram.types import Chat, Message, User

from bot.handlers.start import cmd_start
from bot.middlewares.terms import TermsMiddleware, is_public_command


@pytest.mark.parametrize("text", ["/start", "/start@AltCamSecurityUaBot", "/start signed_link", "/id@AltCamSecurityUaBot"])
def test_public_commands(text):
    assert is_public_command(text)


@pytest.mark.parametrize("text", [None, "hello", "/start_bad", "/admin", "/id_bad"])
def test_nonpublic_commands(text):
    assert not is_public_command(text)


@pytest.mark.asyncio
async def test_addressed_command_bypasses_database_gate():
    user = User(id=123, is_bot=False, first_name="Manager")
    event = Message(message_id=1, date=datetime.now(timezone.utc),
                    chat=Chat(id=-100123, type="supergroup"), from_user=user,
                    text="/start@AltCamSecurityUaBot")
    handler = AsyncMock(return_value="handled")
    with patch("bot.middlewares.terms.SessionLocal", side_effect=AssertionError("DB used")):
        assert await TermsMiddleware()(handler, event, {"event_from_user": user}) == "handled"
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_group_start_responds_without_database_or_captcha():
    message = SimpleNamespace(chat=SimpleNamespace(type="supergroup", id=-100123), answer=AsyncMock())
    state = AsyncMock()
    with patch("bot.handlers.start.SessionLocal", side_effect=AssertionError("DB used")):
        await cmd_start(message, state, CommandObject(command="start"))
    message.answer.assert_awaited_once()
    assert "-100123" in message.answer.call_args.args[0]
    state.update_data.assert_not_awaited()
