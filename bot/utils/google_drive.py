from bot.config import get_settings


async def get_order_card_file_id(order_id: str) -> str | None:
    """Return Telegram file_id for a Drive-backed order card.

    The production integration can map order/category to a Google Drive file,
    download it via aiogoogle/gspread-asyncio, and upload it to Telegram.
    For now the function is intentionally safe: if Drive is not configured,
    the bot tells the client that the manager will prepare the card manually.
    """
    settings = get_settings()
    if not settings.google_service_account_json or not settings.google_drive_folder_id:
        return None
    return None
