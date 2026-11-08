"""Validated public lead contract; persistence/delivery reuse the existing inbox."""
import json
import re
from urllib.parse import urlsplit

SOURCES = {"hero", "quiz", "calculator", "cart", "consultation"}


def normalize_api_lead(data):
    if not isinstance(data, dict) or len(json.dumps(data, allow_nan=False).encode()) > 32768:
        raise ValueError("invalid_payload")
    def field(key, limit, default=""):
        value = data.get(key, default)
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError("invalid_" + key)
        return value.strip()
    if field("website", 200):
        raise ValueError("spam")
    source = field("source_form", 32)
    if source not in SOURCES:
        raise ValueError("invalid_source_form")
    name = field("name", 120)
    phone = re.sub(r"[\s()\-]", "", field("phone", 32))
    if re.fullmatch(r"0\d{9}", phone):
        phone = "+38" + phone
    elif re.fullmatch(r"380\d{9}", phone):
        phone = "+" + phone
    email = field("email", 180)
    if not name or not re.fullmatch(r"\+380\d{9}", phone):
        raise ValueError("invalid_contact")
    if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("invalid_email")
    page = field("page_url", 1000)
    referrer = field("referrer", 1000)
    for value in (page, referrer):
        if value and (urlsplit(value).scheme not in {"https", "http"} or not urlsplit(value).hostname):
            raise ValueError("invalid_url")
    details = data.get("object", {})
    calculation = data.get("calculation", {})
    cart = data.get("cart", [])
    if not isinstance(details, dict) or not isinstance(calculation, dict) or not isinstance(cart, list) or len(cart) > 100:
        raise ValueError("invalid_details")
    # Bound nested values too; do not permit arbitrarily deep user objects.
    def bounded(value, depth=0):
        if depth > 5:
            raise ValueError("details_too_deep")
        if isinstance(value, str) and len(value) > 4000:
            raise ValueError("detail_too_long")
        if isinstance(value, (dict, list)):
            if len(value) > 100:
                raise ValueError("too_many_details")
            for child in (value.values() if isinstance(value, dict) else value):
                bounded(child, depth + 1)
    for value in (details, calculation, cart):
        bounded(value)
    attribution = {key: field(key, 200) for key in
                   ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")}
    attribution["referrer"] = referrer
    comment = field("comment", 4000)
    message = comment + "\n" + "\n".join(
        label + ": " + json.dumps(value, ensure_ascii=False)
        for label, value in (("Об’єкт", details), ("Розрахунок", calculation), ("Сторінка", page))
        if value
    )
    return {"type": source, "source_form": source,
            "client": {"name": name, "phone": phone, "email": email},
            "message": message[:4000], "comment": comment, "page": page, "source": page,
            "details": {"object": details, "quote": calculation, "cart": cart},
            "attribution": attribution}
