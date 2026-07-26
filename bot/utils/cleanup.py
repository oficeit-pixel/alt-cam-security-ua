import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.requests import cleanup_old_portfolio_photos

logger = logging.getLogger(__name__)


async def cleanup_verification_media() -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        count = await cleanup_old_portfolio_photos(session, settings.media_retention_days)
        await session.commit()
    if count:
        logger.info("Cleaned portfolio photos for %s installer profiles", count)


def setup_cleanup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(cleanup_verification_media, "cron", hour=3, minute=15)
    scheduler.start()
    return scheduler
