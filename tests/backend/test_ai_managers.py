from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from bot.ai import runtime
from bot.handlers.pipeline_owner import send_to_client
from bot.pipeline.notify import mirror_manager_text


@pytest.mark.asyncio
async def test_mirror_escapes_output_and_records_reply_mapping():
    bot = SimpleNamespace(send_message=AsyncMock(return_value=SimpleNamespace(message_id=8)))
    with patch("bot.pipeline.notify.get_settings", return_value=SimpleNamespace(managers_chat_id=-100123)), \
         patch("bot.pipeline.notify.owner_keyboard", return_value=None), \
         patch("bot.pipeline.service.add_event", new_callable=AsyncMock) as event:
        assert await mirror_manager_text(bot, AsyncMock(), SimpleNamespace(id=7), "<script>x</script>", "AI")
    assert bot.send_message.call_args.args[0] == -100123
    assert "&lt;script&gt;" in bot.send_message.call_args.args[1]
    assert event.call_args.kwargs["owner_message_id"] == 8


@pytest.mark.asyncio
async def test_group_failure_does_not_break_client_reply():
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("offline")))
    with patch("bot.pipeline.notify.get_settings", return_value=SimpleNamespace(managers_chat_id=-100123)), \
         patch("bot.pipeline.notify.owner_keyboard", return_value=None):
        assert not await mirror_manager_text(bot, AsyncMock(), SimpleNamespace(id=7), "reply", "AI")


@pytest.mark.asyncio
async def test_manager_reply_pauses_ai_before_sending():
    session = AsyncMock()
    inquiry = SimpleNamespace(id=7, client_tg_id=123, status="taken")
    with patch.object(runtime, "pause_from_owner", new_callable=AsyncMock) as pause, \
         patch("bot.pipeline.delivery.send_client_text", new_callable=AsyncMock, return_value=False) as send:
        async def deliver(*args, **kwargs):
            pause.assert_awaited_once()
            session.commit.assert_awaited_once()
            return False
        send.side_effect = deliver
        assert not await send_to_client(None, session, inquiry, "Manager reply", 1)


@pytest.mark.asyncio
async def test_inflight_ai_result_discarded_after_manager_takeover():
    settings = SimpleNamespace(ai_active=True, ai_disclose_bot=False)
    inquiry = SimpleNamespace(id=7, client_tg_id=123)
    consultant = SimpleNamespace(reply=AsyncMock(return_value=SimpleNamespace(text="late reply")))
    with patch.object(runtime, "get_settings", return_value=settings), \
         patch.object(runtime, "is_paused", new_callable=AsyncMock, side_effect=[False, True]), \
         patch.object(runtime, "history", new_callable=AsyncMock, return_value=([{"role":"user", "content":"Привіт"}], True)), \
         patch.object(runtime, "_consultant", new_callable=AsyncMock, return_value=consultant), \
         patch("bot.pipeline.delivery.send_client_text", new_callable=AsyncMock) as send:
        assert await runtime.respond(None, AsyncMock(), inquiry) == "paused"
        send.assert_not_awaited()
