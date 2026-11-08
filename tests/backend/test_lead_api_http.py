"""HTTP contract with fake persistence/delivery; never sends real messages."""
import logging
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from bot.web import site_leads


@pytest.mark.asyncio
@pytest.mark.parametrize('source', ['hero', 'quiz', 'calculator', 'consultation'])
async def test_saved_then_notified_over_http(monkeypatch, source):
    events = []
    async def save(payload, remote):
        events.append('save')
        assert payload['attribution']['utm_source'] == 'test'
        return 42
    async def notify(app, lead_id):
        events.append('notify')
    monkeypatch.setattr(site_leads, 'save_lead', save)
    monkeypatch.setattr(site_leads, '_deliver_saved_lead', notify)
    monkeypatch.setattr(site_leads, 'capture_site_lead', AsyncMock(return_value=None))
    app = web.Application()
    app.update(rate_limits={}, logger=logging.getLogger('test'), bot=None)
    app.router.add_post('/api/lead', site_leads.api_lead)
    async with TestClient(TestServer(app)) as client:
        response = await client.post('/api/lead', json={
            'name': 'Тест', 'phone': '0630000000', 'source_form': source,
            'utm_source': 'test', 'page_url': 'https://example.test/'})
        assert response.status == 200
        assert (await response.json())['ok'] is True
    assert events == ['save', 'notify']


@pytest.mark.asyncio
async def test_cart_preserves_existing_order_pipeline(monkeypatch):
    async def order(request):
        assert request['lead_payload']['items'] == [{'id': 'test', 'quantity': 1}]
        assert request['validated_lead']['source_form'] == 'cart'
        return web.json_response({'ok': True, 'order_number': 'TEST'})
    monkeypatch.setattr(site_leads, 'create_order', order)
    app = web.Application()
    app['rate_limits'] = {}
    app.router.add_post('/api/lead', site_leads.api_lead)
    async with TestClient(TestServer(app)) as client:
        data = {'name': 'Тест', 'phone': '0630000000', 'source_form': 'cart',
                'cart': [{'id': 'test', 'quantity': 1}]}
        assert (await client.post('/api/lead', json=data)).status == 200
        assert (await client.post('/api/lead', json={**data, 'website': 'spam'})).status == 400
        for _ in range(8):
            await client.post('/api/lead', json=data)
        assert (await client.post('/api/lead', json=data)).status == 429
