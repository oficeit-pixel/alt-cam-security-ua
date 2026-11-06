import hashlib
import hmac
import json
from urllib.parse import urlencode

from bot.pipeline.checkout import verified_context, launch_url


def test_telegram_checkout_identity():
    data = {"auth_date": "10000", "user": json.dumps({"id": 123, "first_name": "QA", "is_bot": False})}
    secret = hmac.digest(b"WebAppData", b"test-token", "sha256")
    data["hash"] = hmac.new(secret, "\n".join(f"{k}={v}" for k,v in sorted(data.items())).encode(), hashlib.sha256).hexdigest()
    value = {"init": urlencode(data), "inquiry": "5"}
    assert verified_context(value, "test-token", 10001) == (5, 123)
    assert verified_context(value, "other-token", 10001) is None
    assert verified_context(value, "test-token", 14000) is None
    data["user"] = data["user"].replace("123", "777")
    assert verified_context({**value, "init": urlencode(data)}, "test-token", 10001) is None
    assert launch_url("https://example.org/catalog.html?cart=x", 5) is None
    assert launch_url("https://alt-cam.net.ua/catalog.html#services", 5).endswith("consultation=5&section=services")
