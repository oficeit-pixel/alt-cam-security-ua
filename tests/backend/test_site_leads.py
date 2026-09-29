import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from bot.web import site_leads, shop_admin
from bot.web.lead_store import normalize_lead


def request(payload):
    return SimpleNamespace(json=AsyncMock(return_value=payload), remote="127.0.0.1", headers={}, app={"rate_limits": {}, "logger": logging.getLogger("test"), "bot": None})


def test_lead_text_top_level_fields():
    text = site_leads._lead_text({"name": "Тест", "phone": "0630607088", "object": "Будинок"})
    assert "Тест" in text and "0630607088" in text and "Будинок" in text


def test_lead_text_client_fields():
    text = site_leads._lead_text({"name": "wrong", "client": {"name": "<Тест>", "phone": "+380630607088"}})
    assert "&lt;Тест&gt;" in text and "wrong" not in text


@pytest.mark.parametrize("phone", ["0630607088", "+38 (063) 060-70-88", "380630607088"])
def test_phone_normalization(phone):
    assert normalize_lead({"phone": phone})["client"]["phone"] == "+380630607088"


@pytest.mark.parametrize("payload", [[], None, {"phone":"123"}, {"phone":"0630607088", "message":"x"*4001}, {"phone":"0630607088", "data":"x"*17000}])
def test_invalid_payload(payload):
    with pytest.raises(ValueError): normalize_lead(payload)


@pytest.mark.asyncio
async def test_site_lead_saves_before_telegram(monkeypatch):
    events=[]
    async def save(*args): events.append("save"); return 42
    async def send(*args): events.append("send"); raise OSError("private token")
    monkeypatch.setattr(site_leads,"save_lead",save)
    monkeypatch.setattr(site_leads,"_deliver_saved_lead",send)
    response=await site_leads.site_lead(request({"phone":"0630607088"}))
    assert events==["save","send"]
    assert json.loads(response.text)=={"ok":True,"id":42}


@pytest.mark.asyncio
async def test_site_lead_invalid_phone_400():
    assert (await site_leads.site_lead(request({"phone":"123"}))).status==400


@pytest.mark.asyncio
async def test_site_lead_db_failure_503(monkeypatch):
    monkeypatch.setattr(site_leads,"save_lead",AsyncMock(side_effect=OSError("secret")))
    send=AsyncMock()
    monkeypatch.setattr(site_leads,"_deliver_saved_lead",send)
    response=await site_leads.site_lead(request({"phone":"0630607088"}))
    assert response.status==503 and "secret" not in response.text
    send.assert_not_called()


@pytest.mark.asyncio
async def test_admin_leads_requires_auth():
    with pytest.raises(web.HTTPUnauthorized):
        await shop_admin.list_site_leads(request({}))


@pytest.mark.asyncio
async def test_retry_only_failed_recipient(monkeypatch):
    from bot.web import lead_store
    lead=SimpleNamespace(telegram_sent=False, telegram_delivered=[], telegram_error=None, payload={})
    class Session:
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def scalar(self,query): return lead
        async def commit(self): pass
    monkeypatch.setattr(lead_store,"SessionLocal",Session)
    calls=[]
    async def send(target,*args,**kwargs):
        calls.append(target)
        if target==2: raise OSError("do not store private error")
    bot=SimpleNamespace(send_message=send)
    await lead_store.deliver_lead(1,bot,[1,2],lambda p:"test")
    assert lead.telegram_delivered==["1"] and not lead.telegram_sent
    assert lead.telegram_error=="OSError"
    async def recovered(target,*args,**kwargs): calls.append(target)
    bot.send_message=recovered
    await lead_store.deliver_lead(1,bot,[1,2],lambda p:"test")
    assert calls==[1,2,2] and lead.telegram_sent
    await lead_store.deliver_lead(1,bot,[1,2],lambda p:"test")
    assert calls==[1,2,2]
