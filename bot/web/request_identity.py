"""Durable retry identity, stored atomically with the existing lead/order row."""
import hashlib
import json
import re

from sqlalchemy import select, text


class RequestConflict(ValueError):
    pass


def request_identity(payload):
    key = payload.get("request_id")
    if key is None:
        return None  # Older clients remain supported.
    if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{32}", key):
        raise ValueError("invalid_request_id")
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return {"key": key, "digest": hashlib.sha256(canonical.encode()).hexdigest()}


async def existing_request(session, model, column, identity):
    if identity is None:
        return None
    # Transaction-scoped locks work with pooled connections too. The save and
    # lookup share a transaction; rollback releases the lock without a stale claim.
    lock = int.from_bytes(hashlib.sha256((model.__tablename__ + identity["key"]).encode()).digest()[:8], "big", signed=True)
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
    row = await session.scalar(select(model).where(column["_request"]["key"].astext == identity["key"]).limit(1))
    if row is not None and getattr(row, column.key).get("_request") != identity:
        raise RequestConflict("request_id_conflict")
    return row
