from collections.abc import AsyncGenerator
import asyncio
import logging
from sqlalchemy.engine import make_url

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from bot.config import get_settings


class Base(DeclarativeBase):
    pass


logger = logging.getLogger(__name__)


def normalize_database_url(value: str) -> str:
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if sslmode in {"require", "verify-ca", "verify-full"}:
        query["ssl"] = "require"
    return url.set(query=query).render_as_string(hide_password=False)


def database_connect_args(value: str) -> dict:
    if "-pooler" in (make_url(value).host or ""):
        logger.warning("Database pooler detected: statement caches disabled; prefer a direct Neon endpoint")
        return {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    return {}


settings = get_settings()
database_url = normalize_database_url(settings.database_url)

engine: AsyncEngine = create_async_engine(
    database_url, connect_args=database_connect_args(database_url),
    pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=5,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def create_db_schema() -> None:
    from bot.db import models  # noqa: F401: register every table before create_all
    from bot.db.migrations import migrate_admin_auth, migrate_web_orders

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await migrate_web_orders(conn)
        await migrate_admin_auth(conn)


async def init_db_with_retry() -> bool:
    for attempt in range(5):
        try:
            await asyncio.wait_for(create_db_schema(), timeout=20)
            return True
        except Exception as exc:
            # Exception messages can contain connection credentials. Log type only.
            logger.warning("Database initialization attempt %d/5 failed (%s)", attempt + 1, type(exc).__name__)
            if attempt < 4:
                await asyncio.sleep(min(30, 2 ** (attempt + 1)))
    logger.error("Database unavailable; starting web service in degraded mode")
    return False
