"""Published policies only: FAQ texts of the pipeline (owner's rules) + delivery-and-returns.html."""
from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path

from bot.pipeline import texts

POLICY_FILE = Path(__file__).resolve().parents[2] / "delivery-and-returns.html"
TOPICS = ("payment", "delivery", "warranty", "returns")


def _plain(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


@lru_cache(maxsize=1)
def published_policy() -> str:
    try:
        source = POLICY_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""
    main = re.search(r"<main.*?</main>", source, re.S)
    source = re.sub(r"<(script|style).*?</\1>", "", main.group(0) if main else source, flags=re.S)
    return _plain(source).replace("← Повернутися на сайт ALT-CAM", "").strip()[:4000]


def policy(topic: str) -> dict[str, str]:
    topic = topic if topic in TOPICS else "delivery"
    if topic == "payment":
        text = _plain(texts.faq_payment())
    elif topic == "delivery":
        text = _plain(texts.faq_delivery())
    elif topic == "warranty":
        text = _plain(texts.faq_warranty())
    else:
        text = published_policy()
    return {"topic": topic, "text": text, "source": texts.POLICY_URL}
