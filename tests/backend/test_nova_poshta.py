import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from bot.web import shop_admin


def request(origin=None):
    return SimpleNamespace(headers={} if origin is None else {"Origin": origin},
                           remote="127.0.0.1", app={"rate_limits": {}},
                           match_info={"kind": "cities"}, query={"q": "Київ"})


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", ["https://evil.example", "null", "https://alt-cam.net.ua.evil.example"])
async def test_foreign_origin_never_calls_supplier(monkeypatch, origin):
    client = Mock()
    monkeypatch.setattr(shop_admin, "ClientSession", client)
    assert (await shop_admin.nova_poshta(request(origin))).status == 403
    client.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", [None, "https://alt-cam.net.ua"])
async def test_timeout_is_redacted(monkeypatch, origin):
    monkeypatch.setattr(shop_admin, "ClientSession", Mock(side_effect=TimeoutError("private API key")))
    response = await shop_admin.nova_poshta(request(origin))
    assert response.status == 502
    assert json.loads(response.text)["error"] == "temporarily_unavailable"
    assert "private" not in response.text


@pytest.mark.asyncio
async def test_rate_limit_still_applies():
    req = request("https://alt-cam.net.ua")
    for _ in range(120):
        shop_admin._rate_limit_auth(req, "nova-poshta", 120, 60)
    assert (await shop_admin.nova_poshta(req)).status == 429
