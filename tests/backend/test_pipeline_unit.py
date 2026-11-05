"""Order pipeline unit tests (no database, no Telegram)."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from bot.config import get_settings
from bot.integrations import nova_poshta_tracking as np
from bot.integrations import supplier_stock
from bot.middlewares.terms import pipeline_bypass
from bot.pipeline import links, notify, schedule, service, texts
from bot.pipeline.statuses import STATUS_ORDER, STATUSES, can_transition, next_actions

KYIV = timezone(timedelta(hours=2))  # winter time, matches Europe/Kyiv in November


@pytest.fixture(autouse=True)
def secrets(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "pipeline_link_secret", "unit-test-secret")
    monkeypatch.setattr(settings, "admin_ids", [111])
    monkeypatch.setattr(settings, "admin_chat_id", 111)
    monkeypatch.setattr(settings, "second_contact_chat_id", 222)
    monkeypatch.setattr(settings, "site_lead_group_id", -333)
    yield


# --- state machine -------------------------------------------------------
@pytest.mark.parametrize("status", sorted(service.SLA_ACK_STATUSES))
def test_stale_sla_only_before_manager_acknowledgement(status):
    now = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
    row = SimpleNamespace(status=status, awaiting_since=now - timedelta(minutes=507),
                          last_client_msg_at=now - timedelta(minutes=507),
                          status_history=[{"status": status, "actor": "owner", "at": now.isoformat()}])
    assert service.stale_sla_acknowledgement(row) == now
    row.last_client_msg_at = now + timedelta(seconds=1)
    assert service.stale_sla_acknowledgement(row) is None


@pytest.mark.parametrize("entry", [{}, {"status": "offer_sent", "actor": "client"},
    {"status": "offer_sent", "actor": "owner", "at": "bad"},
    {"status": "offer_sent", "actor": "owner", "at": "2026-11-05T12:00:00"}])
def test_uncertain_legacy_history_keeps_sla(entry):
    now = datetime(2026, 11, 5, 11, tzinfo=timezone.utc)
    row = SimpleNamespace(status="offer_sent", awaiting_since=now, last_client_msg_at=now, status_history=[entry])
    assert service.stale_sla_acknowledgement(row) is None


def test_full_happy_path_is_allowed():
    for current, target in zip(STATUS_ORDER, STATUS_ORDER[1:]):
        assert can_transition(current, target), (current, target)


@pytest.mark.parametrize("current,target,ok", [
    ("new", "stock_checked", True),        # skipping forward is fine
    ("offer_sent", "stock_checked", True),  # one step back (correction)
    ("offer_sent", "new", False),           # two steps back
    ("new", "closed", False),               # cannot close an unsold request
    ("shipped", "closed", True),
    ("paid", "closed", True),
    ("taken", "rejected", True),
    ("rejected", "taken", True),            # reopen
    ("rejected", "paid", False),
    ("closed", "taken", False),
    ("new", "new", False),
    ("new", "bogus", False),
])
def test_transitions(current, target, ok):
    assert can_transition(current, target) is ok


def test_next_actions_always_offer_reject_and_are_valid():
    for status in STATUSES:
        for target in next_actions(status):
            assert can_transition(status, target), (status, target)
        if status not in {"closed", "rejected"}:
            assert "rejected" in next_actions(status)


# --- deep links ----------------------------------------------------------
def test_signed_link_roundtrip_and_tamper():
    param = links.start_param("o", 42)
    assert len(param) <= 64 and param.replace("_", "").isalnum()
    assert links.parse_start_param(param) == ("o", 42)
    assert links.parse_start_param(param.replace("o42", "o43")) is None
    assert links.parse_start_param("site") is None
    assert links.bot_link("l", 7).startswith("https://t.me/AltCamSecurityUaBot?start=l7_")


def test_deeplink_regex_matches_pipeline_params_only():
    import re
    from bot.handlers.pipeline_client import PIPELINE_START
    assert re.match(PIPELINE_START, "/start site")
    assert re.match(PIPELINE_START, "/start site_catalog")
    assert re.match(PIPELINE_START, "/start " + links.start_param("o", 5))
    assert not re.match(PIPELINE_START, "/start client")
    assert not re.match(PIPELINE_START, "/start installer_pro")


# --- working hours / ETA -------------------------------------------------
def test_eta_in_and_out_of_hours():
    tuesday_10 = datetime(2026, 11, 3, 10, 0, tzinfo=KYIV)
    tuesday_22 = datetime(2026, 11, 3, 22, 0, tzinfo=KYIV)
    saturday_20 = datetime(2026, 11, 7, 20, 0, tzinfo=KYIV)
    assert schedule.is_working_time(tuesday_10)
    assert not schedule.is_working_time(tuesday_22)
    assert schedule.eta_text(tuesday_10) == get_settings().reply_eta_text
    assert schedule.eta_text(tuesday_22) == "завтра після 09:00"
    assert schedule.eta_text(saturday_20) == "у понеділок після 09:00"
    assert schedule.before_ship_cutoff(datetime(2026, 11, 3, 12, 59, tzinfo=KYIV))
    assert not schedule.before_ship_cutoff(datetime(2026, 11, 3, 13, 0, tzinfo=KYIV))


# --- escalation ----------------------------------------------------------
@pytest.mark.parametrize("minutes,level", [(0, 0), (4.9, 0), (5, 1), (14, 1), (15, 2), (59, 2), (60, 3), (600, 3)])
def test_reminder_levels(minutes, level):
    assert service.reminder_level_for(minutes, get_settings().reminder_thresholds) == level


def test_escalation_targets_widen_with_level():
    assert notify.escalation_targets(1) == [111]
    assert notify.escalation_targets(2) == [111, 222]
    assert notify.escalation_targets(3) == [111, 222, -333]


def test_reminder_thresholds_parsing(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "reminder_minutes", "60, 5,15,x")
    assert settings.reminder_thresholds == [5, 15, 60]


# --- texts / keyboards ---------------------------------------------------
def test_texts_have_no_prices_and_mention_owner_rules():
    for text in (texts.faq_payment(), texts.faq_delivery(), texts.faq_warranty(), texts.auto_reply(1)):
        assert "₴" not in text and "грн" not in text
    assert "Накладений платіж" in texts.faq_payment() and "Передоплата" in texts.faq_payment()
    assert "13:00" in texts.faq_delivery() and "отримувач" in texts.faq_delivery()
    assert "№1" in texts.auto_reply(1)


def test_faq_override(monkeypatch):
    monkeypatch.setattr(get_settings(), "faq_warranty_text", "Власний текст")
    assert texts.faq_warranty() == "Власний текст"


def _inquiry(**kw):
    base = dict(id=123456, source="site_order", status="new", client_name="Іван <script>", client_username="ivan",
                phone="+380630000000", payment_method=None, ttn=None, awaiting_since=None, summary="", web_order_id=1,
                client_chat_id=555)
    base.update(kw)
    return SimpleNamespace(**base)


def test_owner_keyboard_callbacks_fit_telegram_limit_and_card_escapes():
    order = SimpleNamespace(order_number="WEB-1", subtotal=10, items=[{"id": "viatec-1", "name": "Cam", "quantity": 1}], delivery={})
    for status in STATUSES:
        keyboard = notify.owner_keyboard(_inquiry(status=status), order)
        for row in keyboard.inline_keyboard:
            for button in row:
                assert len(button.callback_data.encode()) <= 64
    keyboard = notify.owner_keyboard(_inquiry(), order)
    data = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert "inq:123456:take" in data and "inq:123456:stock" in data and "inq:123456:tpl:chk" in data
    card = notify.owner_card(_inquiry(), order)
    assert "&lt;script&gt;" in card and "<script>" not in card


def test_no_templates_for_site_lead_without_telegram():
    keyboard = notify.owner_keyboard(_inquiry(client_chat_id=None, web_order_id=None), None)
    data = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert not any(":tpl:" in d or d.endswith(":reply") for d in data)
    assert "inq:123456:take" in data


# --- middleware ----------------------------------------------------------
def _msg(text, chat_type="private"):
    from aiogram.types import Chat, Message, User
    return Message(message_id=1, date=datetime.now(timezone.utc), chat=Chat(id=5, type=chat_type),
                   from_user=User(id=5, is_bot=False, first_name="C"), text=text)


def test_pipeline_bypass_rules():
    assert pipeline_bypass(_msg("Є камера?"), None, 5)
    assert pipeline_bypass(_msg("/start site"), None, 5)
    assert pipeline_bypass(_msg("Є камера?"), "CaptchaState:waiting_for_captcha", 5)
    assert not pipeline_bypass(_msg("/help2"), None, 5)
    assert not pipeline_bypass(_msg("hi", "group"), None, 5)
    assert not pipeline_bypass(_msg("Відповідь"), "ClientQuizSG:object_type", 5)
    assert pipeline_bypass(_msg("anything", "group"), None, 111)  # owner


def test_pipeline_bypass_disabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "capture_before_terms", False)
    assert not pipeline_bypass(_msg("Є камера?"), None, 5)


# --- suppliers / Nova Poshta --------------------------------------------
VIATEC_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?><sitedata><categories><category><id>11</id><title>Камери</title></category></categories>
<products><product><id>2</id><code>99-1</code><url>https://viatec.ua/product/A</url><stock>few</stock></product>
<product><id>5</id><code>99-2</code><url>https://viatec.ua/product/B</url><stock>no</stock></product></products></sitedata>"""


def test_parse_viatec_xml(tmp_path: Path):
    path = tmp_path / "feed.xml"
    path.write_text(VIATEC_SAMPLE, encoding="utf-8")
    parsed = supplier_stock.parse_viatec_xml(path)
    assert parsed["2"] == {"stock": "few", "url": "https://viatec.ua/product/A", "code": "99-1"}
    assert parsed["5"]["stock"] == "no"


def test_viatec_feeds_come_from_repo_config():
    urls = supplier_stock.viatec_feed_urls()
    assert urls and all(u.startswith("https://viatec.ua/files/") for u in urls)


@pytest.mark.parametrize("value,label", [("+++", "є в наявності (+++)"), ("0", "немає"), ("", "немає"), (None, "немає"), (7, "є в наявності (7)")])
def test_yugtorg_label(value, label):
    assert supplier_stock.yugtorg_stock_label(value) == label


def test_yugtorg_count_found_in_nested_payload():
    assert supplier_stock._find_count({"product": [{"id": 1, "count": "++"}]}) == "++"


@pytest.mark.asyncio
async def test_check_items_uses_cache_and_marks_unknown(monkeypatch):
    async def fake_viatec(force=False):
        return {"2": {"stock": "yes", "url": "https://viatec.ua/product/A", "code": "c"}}
    monkeypatch.setattr(supplier_stock, "load_viatec_stock", fake_viatec)
    monkeypatch.setattr(get_settings(), "yugtorg_api_key", None)
    rows = await supplier_stock.check_items([
        {"id": "viatec-2", "name": "A"}, {"id": "viatec-9", "name": "B"}, {"id": "yugtorg-1", "name": "C"}, {"id": "service-video", "name": "D"}])
    assert [r["stock"] for r in rows] == ["є в наявності", "немає у фіді (знято/невідомо)", "не налаштовано (YUGTORG_API_KEY)", "перевірити вручну"]


@pytest.mark.parametrize("code,kind", [("7", "arrived"), ("8", "arrived"), ("9", "received"), ("11", "received"),
                                       ("103", "problem"), ("5", "in_transit"), ("", None)])
def test_np_classify(code, kind):
    assert np.classify(code) == kind


def test_np_ttn_normalize():
    assert np.normalize_ttn("2045 0296 3396 88") == "20450296339688"
    assert np.normalize_ttn("123") is None


# --- owner decisions (Nov 2026): ETA, auto-registration, Telegram Business --------------------
def test_default_reply_promise_is_5_10_minutes():
    from bot.config import Settings

    assert Settings.model_fields["reply_eta_text"].default == "протягом 5–10 хвилин"


@pytest.mark.parametrize("username,role", [("OficeITHelp", "owner"), ("@oficeithelp", "owner"), ("uniwar", "second"),
                                           ("UniWar", "second"), ("someone", None), (None, None), ("", None)])
def test_contact_roles_by_username(username, role):
    assert get_settings().contact_role_for_username(username) == role


def test_registered_contacts_are_fallback_only(monkeypatch):
    from bot.handlers.admin import is_admin
    from bot.pipeline import contacts

    settings = get_settings()
    contacts.set_cache({"owner": 900, "second": 901})
    try:
        assert settings.owner_chat_id == 111 and settings.second_contact_target == 222  # env wins
        monkeypatch.setattr(settings, "admin_ids", [])
        monkeypatch.setattr(settings, "admin_chat_id", None)
        monkeypatch.setattr(settings, "second_contact_chat_id", None)
        assert settings.owner_chat_id == 900 and settings.second_contact_target == 901
        assert notify.escalation_targets(2) == [900, 901]
        assert is_admin(900) and is_admin(901) and not is_admin(902)
    finally:
        contacts.set_cache({})


def test_business_ack_is_first_person_and_respects_hours(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "reply_eta_text", "протягом 5–10 хвилин")
    monkeypatch.setattr(settings, "business_autoreply_text", None)
    assert texts.business_ack(datetime(2026, 11, 3, 10, 0, tzinfo=KYIV)) == "Отримав, відповім протягом 5–10 хвилин."
    assert texts.business_ack(datetime(2026, 11, 3, 22, 0, tzinfo=KYIV)) == "Отримав, відповім завтра після 09:00."
    monkeypatch.setattr(settings, "business_autoreply_text", "Дякую, скоро відповім")
    assert texts.business_ack() == "Дякую, скоро відповім"


def test_bot_texts_never_claim_to_be_human():
    bot_texts = [texts.auto_reply(1), texts.faq_human(), texts.taken_text(1), texts.followup_text(1)]
    for text in bot_texts:
        assert "Отримав" not in text and "я менеджер" not in text.lower()


def test_business_confirm_template_has_no_button_reference():
    assert "кнопкою" in texts.template_text("cnf") and "кнопк" not in texts.template_text("cnf", business=True)
    assert texts.template_text("yes", business=True) == texts.template_text("yes")


def test_business_connection_only_for_owner(monkeypatch):
    from bot.handlers.pipeline_business import connection_allowed

    assert connection_allowed(111, None)            # ADMIN_CHAT_ID
    assert connection_allowed(5, "OficeITHelp")     # owner username
    assert not connection_allowed(5, "uniwar")      # second contact cannot connect his own account
    assert not connection_allowed(5, "stranger")


def test_business_ignore_list_parsing(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "business_ignore_chat_ids", "12, -34,abc,")
    assert settings.business_ignored_ids == {12, -34}


def test_np_job_disabled_without_key(monkeypatch):
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from bot.pipeline import jobs

    settings = get_settings()
    monkeypatch.setattr(settings, "pipeline_scheduler_enabled", True)
    monkeypatch.setattr(settings, "nova_poshta_api_key", None)
    scheduler = AsyncIOScheduler()
    assert jobs.setup_pipeline_jobs(scheduler, object())
    assert "pipeline_np_tracking" not in {job.id for job in scheduler.get_jobs()}
    monkeypatch.setattr(settings, "nova_poshta_api_key", "k")
    scheduler = AsyncIOScheduler()
    jobs.setup_pipeline_jobs(scheduler, object())
    assert "pipeline_np_tracking" in {job.id for job in scheduler.get_jobs()}
