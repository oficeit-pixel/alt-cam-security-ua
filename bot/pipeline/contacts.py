"""Auto-registered owner / second contact chat ids.

Numeric Telegram ids are often unknown at deploy time. When a user whose username is listed in
OWNER_USERNAMES / SECOND_CONTACT_USERNAMES presses /start, their chat id is stored in `pipeline_contacts`
and used whenever ADMIN_CHAT_ID / ADMIN_IDS / SECOND_CONTACT_CHAT_ID are not set. First registration wins:
to move a role to another account, set the env variable or delete the row.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import PipelineContact

logger = logging.getLogger("altcam.pipeline.contacts")
ROLES = ("owner", "second")
_cache: dict[str, int] = {}


def registered_chat_id(role: str) -> int | None:
    return _cache.get(role)


def registered_ids() -> set[int]:
    return set(_cache.values())


def set_cache(values: dict[str, int]) -> None:
    """Testing / startup helper."""
    _cache.clear()
    _cache.update(values)


async def load(session: AsyncSession) -> dict[str, int]:
    rows = (await session.scalars(select(PipelineContact))).all()
    set_cache({row.role: row.chat_id for row in rows if row.role in ROLES})
    return dict(_cache)


async def safe_reload() -> None:
    from bot.db.base import SessionLocal

    try:
        async with SessionLocal() as session:
            await load(session)
    except Exception as exc:  # table may not exist yet on first boot
        logger.warning("pipeline_contacts_load_failed (%s)", type(exc).__name__)


async def register(session: AsyncSession, role: str, chat_id: int, username: str | None) -> str:
    """Returns 'registered' | 'already' | 'taken' (role held by another chat)."""
    if role not in ROLES:
        raise ValueError(role)
    row = await session.get(PipelineContact, role)
    if row is None:
        session.add(PipelineContact(role=role, chat_id=chat_id, username=(username or "")[:64] or None))
        await session.flush()
        _cache[role] = chat_id
        logger.info("pipeline_contact_registered role=%s chat=%s", role, chat_id)
        return "registered"
    _cache[role] = row.chat_id
    if row.chat_id == chat_id:
        if username and row.username != username[:64]:
            row.username = username[:64]
        return "already"
    return "taken"
