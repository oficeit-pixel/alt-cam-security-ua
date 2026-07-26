import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.handlers.admin import CHANNEL_NAVIGATION_TEXT
from bot.keyboards.common import channel_navigation_keyboard


async def main() -> None:
    settings = get_settings()
    if not settings.channel_id:
        raise RuntimeError("CHANNEL_ID is not configured")
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        message = await bot.send_message(
            settings.channel_id,
            CHANNEL_NAVIGATION_TEXT,
            reply_markup=channel_navigation_keyboard(),
            disable_web_page_preview=True,
        )
        try:
            await bot.pin_chat_message(
                settings.channel_id,
                message.message_id,
                disable_notification=True,
            )
            print(f"published_and_pinned:{message.message_id}")
        except Exception as exc:
            print(f"published_not_pinned:{message.message_id}:{exc}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
