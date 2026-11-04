"""Send a message to the client where they last wrote: the bot chat or the owner's Telegram Business chat."""
from __future__ import annotations

import logging

from bot.db.models import Inquiry

logger = logging.getLogger("altcam.pipeline.delivery")


def is_business(inquiry: Inquiry) -> bool:
    return bool(inquiry.business_connection_id)


async def send_client_text(bot, inquiry: Inquiry, text: str, reply_markup=None) -> bool:
    """Business chats: plain text on behalf of the owner (only for owner-initiated actions and the optional
    acknowledgement); keyboards are only attached in the bot chat."""
    if bot is None or not inquiry.client_chat_id:
        return False
    try:
        if inquiry.business_connection_id:
            await bot.send_message(inquiry.client_chat_id, text, business_connection_id=inquiry.business_connection_id,
                                   disable_web_page_preview=True)
        else:
            await bot.send_message(inquiry.client_chat_id, text, reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception as exc:
        logger.warning("client_send_failed inquiry=%s business=%s (%s)", inquiry.id, is_business(inquiry), type(exc).__name__)
        return False
    return True
