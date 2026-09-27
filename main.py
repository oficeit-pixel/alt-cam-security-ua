import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.db.base import init_db_with_retry, engine
from bot.handlers import admin, auction, client_quiz, group_guide, installer, service, start
from bot.middlewares import captcha
from bot.middlewares.terms import TermsMiddleware
from bot.utils.cleanup import setup_cleanup_scheduler
from bot.web.site_leads import start_site_lead_server


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    if settings.auto_create_db:
        await init_db_with_retry()
    scheduler = setup_cleanup_scheduler()
    bot = None
    site_lead_runner = None

    if settings.bot_token:
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    site_lead_runner = await start_site_lead_server(bot)

    if bot is None or not settings.enable_bot_polling:
        logging.info("Web CRM running without Telegram polling (disabled or unconfigured)")
        try:
            await asyncio.Event().wait()
        finally:
            scheduler.shutdown(wait=False)
            await site_lead_runner.cleanup()
            await engine.dispose()
            if bot is not None:
                await bot.session.close()
        return

    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(TermsMiddleware())
    dp.callback_query.middleware(TermsMiddleware())
    dp.include_router(captcha.router)
    dp.include_router(group_guide.router)
    dp.include_router(start.router)
    dp.include_router(client_quiz.router)
    dp.include_router(service.router)
    dp.include_router(installer.router)
    dp.include_router(auction.router)
    dp.include_router(admin.router)

    await bot.delete_webhook(drop_pending_updates=False)
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await site_lead_runner.cleanup()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
