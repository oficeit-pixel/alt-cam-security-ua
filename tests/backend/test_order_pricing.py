import pytest
from bot.web.order_pricing import installation_quote


@pytest.mark.parametrize("indoor,outdoor,total", [(2, 0, 2550), (2, 2, 4350), (4, 4, 6150), (0, 0, 0), (1, 0, 2050), (0, 1, 2150), (9, 0, 5450)])
def test_shared_rates(indoor, outdoor, total):
    config, amount = installation_quote(dict(indoor=indoor, outdoor=outdoor, nvr=True, mobile=True, price=1))
    assert amount == total
    assert "price" not in config


@pytest.mark.parametrize("value", [None, [], {"indoor": -1}, {"outdoor": 101}, {"indoor": 1.5}, {"indoor": True}, {"indoor": "2"}, {"nvr": "false"}])
def test_invalid_installation(value):
    with pytest.raises(ValueError):
        installation_quote(value)


def test_unspecified_service_packages_are_quote_only():
    from bot.web.site_leads import SERVICE_CATALOG
    assert all(price == 0 for name, price in SERVICE_CATALOG.values())


@pytest.mark.asyncio
async def test_order_persists_server_total_and_quote_flag(monkeypatch):
    import json
    import logging
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from bot.web import site_leads
    saved = []
    class Session:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def add(self, order):
            order.id = 1
            saved.append(order)
        async def commit(self): pass
        async def refresh(self, order): pass
        async def scalars(self, *args): return SimpleNamespace(all=lambda: [])
    class Request(dict): pass
    request = Request()
    request.remote = "127.0.0.1"
    request.headers = {}
    request.app = {"rate_limits": {}, "logger": logging.getLogger("test"), "bot": None}
    request.json = AsyncMock(return_value={
        "customer": {"name": "Test", "phone": "+380630000000"},
        "delivery": {"type": "pickup"},
        "items": [{"id": "camera", "quantity": 2, "price": 1}, {"id": "service-ajax", "type": "service", "quantity": 1}],
        "needs_installation": True,
        "installation": {"indoor": 2, "outdoor": 0, "nvr": True, "mobile": True, "price": 1},
    })
    monkeypatch.setattr(site_leads, "SessionLocal", Session)
    monkeypatch.setattr(site_leads, "_feed_catalog", lambda: {"camera": ("Test camera", 1000)})
    monkeypatch.setattr(site_leads, "auto_create_order_drive_folder", AsyncMock())
    monkeypatch.setattr(site_leads, "capture_site_order", AsyncMock(return_value=None))
    monkeypatch.setattr(site_leads, "_post_order_notifications", AsyncMock())
    response = await site_leads.create_order(request)
    assert response.status == 200
    assert json.loads(response.text)["ok"]
    order = saved[0]
    assert order.subtotal == 4550
    assert order.delivery["price_breakdown"] == {"equipment": 2000, "installation": 2550, "total": 4550, "quote_required": True}
    assert sum(item["price"] * item["quantity"] for item in order.items) == order.subtotal
    assert order.items[1]["quote_required"] is True
