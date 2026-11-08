"""Offline tests: never contact Telegram or production databases."""
import pytest
from bot.web.lead_api import normalize_api_lead


@pytest.mark.parametrize("source", ["hero", "quiz", "calculator", "cart", "consultation"])
def test_each_form_contract(source):
    result = normalize_api_lead({"name": "Тест", "phone": "0630000000",
        "source_form": source, "object": {"walls": "бетон", "height": 3},
        "calculation": {"cameras": 4}, "utm_source": "test",
        "page_url": "https://example.test/", "cart": []})
    assert result["client"]["phone"] == "+380630000000"
    assert result["attribution"]["utm_source"] == "test"
    assert result["details"]["object"]["walls"] == "бетон"


@pytest.mark.parametrize("change", [
    {"website": "spam"}, {"phone": "123"}, {"email": "bad"},
    {"name": "x" * 121}, {"source_form": "invalid"},
    {"object": "not an object"}, {"comment": "x" * 4001},
    {"page_url": "javascript:alert(1)"}])
def test_invalid_requests(change):
    with pytest.raises(ValueError):
        normalize_api_lead({"name": "Тест", "phone": "0630000000", "source_form": "hero", **change})
