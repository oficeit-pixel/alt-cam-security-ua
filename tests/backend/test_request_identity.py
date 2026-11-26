import pytest
from bot.web.request_identity import request_identity


def test_legacy_requests_and_canonical_digest():
    assert request_identity({}) is None
    assert request_identity({"request_id": "a" * 32, "name": "Тест"}) == request_identity({"name": "Тест", "request_id": "a" * 32})
    assert request_identity({"request_id": "a" * 32, "name": "A"}) != request_identity({"request_id": "a" * 32, "name": "B"})


@pytest.mark.parametrize("key", ["", "a", "x" * 32, "a" * 100, 1, {}, []])
def test_invalid_request_identity(key):
    with pytest.raises(ValueError):
        request_identity({"request_id": key})
