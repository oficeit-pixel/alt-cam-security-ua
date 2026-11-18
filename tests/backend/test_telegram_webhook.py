import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from aiogram import Bot, Dispatcher
from bot.web.telegram_webhook import validate_url, webhook_secret, activate_webhook, register_webhook

URL = 'https://example.org/telegram/webhook'
TOKEN = '123456:TEST_TOKEN_NOT_A_REAL_SECRET'

@pytest.mark.parametrize('url', [URL+'/', ' '+URL+' ', '\n'+URL+'\r\n', '\u00a0'+URL+'/\u00a0'])
def test_normalizes_dashboard_whitespace_and_trailing_slash(url):
    assert validate_url(url) == URL

def test_scheduler_runs_for_webhook_unless_explicitly_disabled():
    from bot.config import Settings
    settings = Settings(TELEGRAM_WEBHOOK_URL=URL, ENABLE_BOT_POLLING=False)
    assert settings.scheduler_active is True
    settings.pipeline_scheduler_enabled = False
    assert settings.scheduler_active is False

@pytest.mark.parametrize('url', ['http://example.org/telegram/webhook', 'https://example.org/other',
    'https://user:password@example.org/telegram/webhook', URL+'?token=x', URL+'#fragment',
    'https://example.org/telegram/ webhook', 'https://example.org', 'https://example.org/telegram/webhook//'])
def test_rejects_unsafe_url(url):
    with pytest.raises(ValueError): validate_url(url)

def test_secret_is_stable_domain_separated_and_token_specific():
    assert validate_url(URL) == URL
    assert len(webhook_secret(TOKEN)) == 64
    assert webhook_secret(TOKEN) == webhook_secret(TOKEN)
    assert webhook_secret(TOKEN) != webhook_secret(TOKEN+'other')
    assert TOKEN not in webhook_secret(TOKEN)

@pytest.mark.asyncio
async def test_activation_preserves_pending_updates():
    bot = SimpleNamespace(token=TOKEN, set_webhook=AsyncMock())
    dp = SimpleNamespace(resolve_used_update_types=lambda:['message','callback_query'])
    await activate_webhook(bot, dp, URL)
    args = bot.set_webhook.call_args.kwargs
    assert args['drop_pending_updates'] is False
    assert args['max_connections'] == 1
    assert args['secret_token'] == webhook_secret(TOKEN)

@pytest.mark.asyncio
async def test_endpoint_rejects_forged_updates_before_dispatch():
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.feed_webhook_update = AsyncMock(return_value=None)
    app = web.Application()
    register_webhook(app, dp, bot, URL)
    async with TestClient(TestServer(app)) as client:
        for headers in ({}, {'X-Telegram-Bot-Api-Secret-Token':'wrong'}):
            response = await client.post('/telegram/webhook', json={'update_id':123}, headers=headers)
            assert response.status == 401
        dp.feed_webhook_update.assert_not_awaited()
        response = await client.post('/telegram/webhook', json={'update_id':123},
            headers={'X-Telegram-Bot-Api-Secret-Token':webhook_secret(TOKEN)})
        assert response.status == 200
        dp.feed_webhook_update.assert_awaited_once()
