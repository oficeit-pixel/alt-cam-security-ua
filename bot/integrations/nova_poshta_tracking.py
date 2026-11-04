"""Nova Poshta TTN tracking: TrackingDocument.getStatusDocuments (up to 100 TTNs per call)."""
from __future__ import annotations

import logging
import re
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from bot.config import get_settings

logger = logging.getLogger("altcam.np_tracking")
NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"
TTN_PATTERN = re.compile(r"^\d{14}$")
ARRIVED = {"7", "8"}
RECEIVED = {"9", "10", "11", "106"}
REFUSED = {"102", "103", "105", "111", "113", "141", "144"}


def normalize_ttn(value: str) -> str | None:
    digits = re.sub(r"[\s-]", "", value or "")
    return digits if TTN_PATTERN.fullmatch(digits) else None


def classify(code: str | int | None) -> str | None:
    code = str(code or "")
    if code in ARRIVED:
        return "arrived"
    if code in RECEIVED:
        return "received"
    if code in REFUSED:
        return "problem"
    return "in_transit" if code else None


async def fetch_statuses(documents: list[tuple[str, str | None]]) -> dict[str, dict[str, str]]:
    """documents: [(ttn, phone_or_None)] -> {ttn: {"code": "7", "status": "..."}}"""
    settings = get_settings()
    if not documents:
        return {}
    body = {
        "apiKey": settings.nova_poshta_api_key or "",
        "modelName": "TrackingDocument",
        "calledMethod": "getStatusDocuments",
        "methodProperties": {"Documents": [
            {"DocumentNumber": ttn, **({"Phone": re.sub(r"\D", "", phone)} if phone else {})}
            for ttn, phone in documents[:100]
        ]},
    }
    async with ClientSession(timeout=ClientTimeout(total=20)) as client:
        async with client.post(NP_API_URL, json=body) as response:
            response.raise_for_status()
            data: Any = await response.json(content_type=None)
    if not isinstance(data, dict) or not data.get("success"):
        raise RuntimeError("nova_poshta_tracking_failed")
    result = {}
    for row in data.get("data", []):
        if isinstance(row, dict) and row.get("Number"):
            result[str(row["Number"])] = {"code": str(row.get("StatusCode", "")), "status": str(row.get("Status", ""))}
    return result
