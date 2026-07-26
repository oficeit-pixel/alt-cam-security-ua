from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import get_settings
from bot.keyboards.common import channel_navigation_keyboard

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    settings = get_settings()
    return user_id in settings.admin_ids or user_id == settings.admin_chat_id


CHANNEL_NAVIGATION_TEXT = (
    "<b>ALT-CAM Security UA</b>\n\n"
    "Оберіть, що вам потрібно:\n\n"
    "<b>Клієнтам:</b>\n"
    "• підібрати відеоспостереження, домофон, Ajax або UPS;\n"
    "• отримати консультацію;\n"
    "• зробити попередній розрахунок;\n"
    "• залишити заявку на монтаж або сервіс.\n\n"
    "<b>Монтажникам:</b>\n"
    "• пройти анкету;\n"
    "• підтвердити рівень;\n"
    "• отримати доступ до закритої групи замовлень після перевірки.\n\n"
    "Натисніть потрібну кнопку нижче."
)


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Команда доступна тільки адміністратору.")
        return
    await message.answer(
        "Адмін-панель ALT-CAM\n\n"
        "Доступні дії зараз:\n"
        "/id - отримати ID чату\n"
        "/navigation_preview - показати пост-навігацію\n"
        "/publish_navigation - опублікувати пост у канал з CHANNEL_ID\n"
        "/delete_me - видалити власні персональні дані\n\n"
        "Модерація монтажників виконується inline-кнопками в анкетах."
    )


@router.message(Command("navigation_preview"))
async def navigation_preview(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Команда доступна тільки адміністратору.")
        return
    await message.answer(CHANNEL_NAVIGATION_TEXT, reply_markup=channel_navigation_keyboard())


@router.message(Command("publish_navigation"))
async def publish_navigation(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Команда доступна тільки адміністратору.")
        return
    settings = get_settings()
    if not settings.channel_id:
        await message.answer(
            "CHANNEL_ID ще не вказаний у налаштуваннях.\n\n"
            "Поки можна використати /navigation_preview і вручну переслати або скопіювати пост у канал."
        )
        return
    await message.bot.send_message(
        settings.channel_id,
        CHANNEL_NAVIGATION_TEXT,
        reply_markup=channel_navigation_keyboard(),
        disable_web_page_preview=True,
    )
    await message.answer("Навігаційний пост опубліковано в канал. Тепер його потрібно закріпити.")
