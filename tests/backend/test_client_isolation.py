from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.handlers import pipeline_client, pipeline_owner


@pytest.mark.asyncio
@pytest.mark.parametrize("quoted_id", [2, None])
async def test_pending_reply_cannot_send_another_clients_quoted_message(quoted_id):
    message = SimpleNamespace(from_user=SimpleNamespace(id=111), chat=SimpleNamespace(id=-100123),
                              reply_to_message=SimpleNamespace(message_id=9), answer=AsyncMock())
    state = AsyncMock()
    state.get_data.return_value = {"inquiry_id": 1}
    session = AsyncMock()
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    with patch.object(pipeline_owner, "is_admin", return_value=True), \
         patch.object(pipeline_owner, "SessionLocal", factory), \
         patch.object(pipeline_owner.service, "inquiry_by_owner_message", new_callable=AsyncMock,
                      return_value=SimpleNamespace(id=quoted_id) if quoted_id else None), \
         patch.object(pipeline_owner, "relay_owner_message", new_callable=AsyncMock) as relay:
        await pipeline_owner.owner_reply_text(message, state)
    relay.assert_not_awaited()
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_cannot_use_order_button_in_group():
    callback = SimpleNamespace(message=SimpleNamespace(chat=SimpleNamespace(type="supergroup", id=-123)),
                               from_user=SimpleNamespace(id=555), answer=AsyncMock())
    with patch.object(pipeline_client, "SessionLocal", side_effect=AssertionError("must not read orders")):
        await pipeline_client.client_decision(callback)
    callback.answer.assert_awaited_once()
