import asyncio
import json
from unittest.mock import AsyncMock
from types import SimpleNamespace

import pytest
from aiohttp import ClientSession
from sqlalchemy.engine import make_url
from bot.db import base
from bot.web import site_leads


@pytest.mark.parametrize('source,ssl', [
    ('postgresql://u:p@ep-test.neon.tech/db?sslmode=require&channel_binding=require', 'require'),
    ('postgres://u:p@render/db', None),
    ('postgresql://u:p@ep-test-pooler.neon.tech/db?sslmode=verify-full', 'require'),
    ('postgresql://u:p@localhost/db', None),
])
def test_normalize(source, ssl):
    url = make_url(base.normalize_database_url(source))
    assert url.drivername == 'postgresql+asyncpg'
    assert 'sslmode' not in url.query and 'channel_binding' not in url.query
    assert url.query.get('ssl') == ssl
    assert url.password == 'p'


def test_pooler(caplog):
    assert base.database_connect_args('postgresql://u:secret@ep-x-pooler.neon.tech/db') == {
        'statement_cache_size': 0, 'prepared_statement_cache_size': 0}
    assert 'secret' not in caplog.text
    assert base.database_connect_args('postgresql://u:p@ep-x.neon.tech/db') == {}


def test_encoded_password():
    url = make_url(base.normalize_database_url('postgresql://u:p%40ss%2Fword@ep-x/db?ssl=require'))
    assert url.password == 'p@ss/word'
    assert url.query['ssl'] == 'require'


@pytest.mark.asyncio
async def test_retry_failure(monkeypatch, caplog):
    create = AsyncMock(side_effect=OSError('secret connection string'))
    sleep = AsyncMock()
    monkeypatch.setattr(base, 'create_db_schema', create)
    monkeypatch.setattr(base.asyncio, 'sleep', sleep)
    assert await base.init_db_with_retry() is False
    assert create.await_count == 5
    assert [call.args[0] for call in sleep.await_args_list] == [2, 4, 8, 16]
    assert 'secret connection string' not in caplog.text


@pytest.mark.asyncio
async def test_retry_success(monkeypatch):
    monkeypatch.setattr(base, 'create_db_schema', AsyncMock())
    assert await base.init_db_with_retry() is True


@pytest.mark.asyncio
async def test_server_starts_without_database():
    # Real refused TCP connection, not a mocked database result.
    runner = await site_leads.start_site_lead_server(None)
    try:
        port = runner.addresses[0][1]
        async with ClientSession() as client:
            async with client.get(f'http://127.0.0.1:{port}/health') as response:
                assert response.status == 200
                assert await response.json() == {'ok': True, 'db': False}
    finally:
        await runner.cleanup()
        await base.engine.dispose()


@pytest.mark.asyncio
async def test_health_success(monkeypatch):
    class Connection:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def execute(self, sql): assert str(sql) == 'SELECT 1'
    monkeypatch.setattr(site_leads, 'engine', SimpleNamespace(connect=Connection))
    assert json.loads((await site_leads.health(None)).text) == {'ok': True, 'db': True}


@pytest.mark.asyncio
async def test_main_continues_without_db_and_polling(monkeypatch):
    import main as entry
    from unittest.mock import Mock
    settings = SimpleNamespace(auto_create_db=True,bot_token='test',enable_bot_polling=False)
    monkeypatch.setattr(entry,'get_settings',lambda:settings)
    init = AsyncMock(return_value=False)
    monkeypatch.setattr(entry,'init_db_with_retry',init)
    bot = SimpleNamespace(session=SimpleNamespace(close=AsyncMock()),delete_webhook=AsyncMock())
    monkeypatch.setattr(entry,'Bot',lambda **kwargs:bot)
    scheduler = SimpleNamespace(shutdown=Mock())
    monkeypatch.setattr(entry,'setup_cleanup_scheduler',lambda:scheduler)
    runner = SimpleNamespace(cleanup=AsyncMock())
    started = asyncio.Event()
    async def start(bot): started.set(); return runner
    monkeypatch.setattr(entry,'start_site_lead_server',start)
    task = asyncio.create_task(entry.main())
    await asyncio.wait_for(started.wait(), 2)
    assert not task.done()
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    init.assert_awaited_once()
    bot.delete_webhook.assert_not_called()
    runner.cleanup.assert_awaited_once()
