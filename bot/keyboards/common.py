from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.config import get_settings


def main_menu() -> InlineKeyboardMarkup:
    settings = get_settings()
    builder = InlineKeyboardBuilder()
    builder.button(text="📹 Відеоспостереження", callback_data="category:cctv")
    builder.button(text="🚪 Домофонія та СКУД", callback_data="category:intercom")
    builder.button(text="🚨 Сигналізація Ajax", callback_data="category:ajax")
    builder.button(text="🔋 UPS та Резервне живлення", callback_data="category:ups")
    builder.button(text="🌐 Розширений калькулятор на сайті", url=settings.calculator_url)
    builder.button(text="🛠️ Виклик майстра / Сервіс", callback_data="service:start")
    builder.button(text="👷 Для монтажників", callback_data="installer:start")
    builder.adjust(1)
    return builder.as_markup()


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back:main")]]
    )


def back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data)]]
    )


def installer_track_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Новачок: хочу навчитись і брати сервіс", callback_data="installer:track:newbie")],
            [InlineKeyboardButton(text="Монтажник: маю досвід і портфоліо", callback_data="installer:track:pro")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:main")],
        ]
    )


def accept_terms_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚖️ Погоджуюсь з Офертою та ПД",
                    callback_data="terms:accept",
                )
            ],
            [
                InlineKeyboardButton(text="Оферта", url=settings.terms_url),
                InlineKeyboardButton(text="Політика ПД", url=settings.privacy_url),
            ],
        ]
    )


def captcha_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    variants = [("📹 Відеокамера", "camera"), ("🚗 Авто", "car"), ("🍕 Піца", "pizza"), ("🎧 Навушники", "headphones")]
    for label, value in variants:
        builder.button(text=label, callback_data=f"captcha:{value}")
    builder.adjust(2)
    return builder.as_markup()


def object_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in ["Приватний будинок", "Офіс/Магазин", "Склад", "Квартира"]:
        builder.button(text=item, callback_data=f"object:{item}")
    builder.button(text="⬅️ Назад", callback_data="back:main")
    builder.adjust(1)
    return builder.as_markup()


def points_count_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in ["1-2 точки", "3-4 точки", "5-8 точок", "9+ точок", "Не знаю"]:
        builder.button(text=item, callback_data=f"points:{item}")
    builder.button(text="⬅️ Назад", callback_data="back:client:object")
    builder.adjust(1)
    return builder.as_markup()


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Так", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="Ні", callback_data=f"{prefix}:no"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:client:points")],
        ]
    )


def photo_upload_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Готово, перейти до розрахунку", callback_data="photos:done")],
            [InlineKeyboardButton(text="Пропустити фото", callback_data="photos:skip")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:client:ups")],
        ]
    )


def order_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Знайти перевіреного монтажника", callback_data=f"order:publish:{order_id}")],
            [InlineKeyboardButton(text="💾 Завантажити картку з Google Drive", callback_data=f"drive:card:{order_id}")],
            [InlineKeyboardButton(text="Калькулятор на сайті", url=settings.calculator_url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:client:photos")],
        ]
    )


def service_fault_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in [
        "Не працюють камери",
        "Збився доступ Hik-Connect/DMSS",
        "Заміна диска",
        "Проблеми з UPS",
    ]:
        builder.button(text=item, callback_data=f"fault:{item}")
    builder.button(text="⬅️ Назад", callback_data="back:main")
    builder.adjust(1)
    return builder.as_markup()


def installer_test_keyboard(question_index: int, options: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, option in enumerate(options):
        builder.button(text=option, callback_data=f"test:{question_index}:{idx}")
    builder.adjust(1)
    return builder.as_markup()


def admin_installer_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрити", callback_data=f"installer:approve:{user_id}"),
                InlineKeyboardButton(text="❌ Відхилити", callback_data=f"installer:reject:{user_id}"),
            ]
        ]
    )


def auction_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✋ Відгукнутися на замовлення", callback_data=f"bid:start:{order_id}")]
        ]
    )


def client_bid_keyboard(bid_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Обрати цього майстра", callback_data=f"bid:accept:{bid_id}")]
        ]
    )


def contact_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Перейти на сайт", url=settings.site_url)]]
    )


def group_guide_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Я користувач / хочу систему", callback_data="guide:client")],
            [InlineKeyboardButton(text="Потрібен сервіс або налаштування", callback_data="guide:service")],
            [InlineKeyboardButton(text="Я новачок / хочу монтажити", callback_data="guide:installer_newbie")],
            [InlineKeyboardButton(text="Я монтажник / хочу замовлення", callback_data="guide:installer_pro")],
            [
                InlineKeyboardButton(
                    text="🤖 Відкрити бота",
                    url=f"https://t.me/{settings.bot_username}?start=group",
                ),
                InlineKeyboardButton(text="🌐 Сайт", url=settings.site_url),
            ],
        ]
    )


def guide_private_keyboard(intent: str = "group") -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити бота",
                    url=f"https://t.me/{settings.bot_username}?start={intent}",
                )
            ],
            [InlineKeyboardButton(text="Калькулятор на сайті", url=settings.calculator_url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="guide:menu")],
        ]
    )


def channel_navigation_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    rows = [
        [
            InlineKeyboardButton(
                text="Я клієнт / хочу систему",
                url=f"https://t.me/{settings.bot_username}?start=client",
            )
        ],
        [
            InlineKeyboardButton(
                text="Потрібен сервіс / налаштування",
                url=f"https://t.me/{settings.bot_username}?start=service",
            )
        ],
        [
            InlineKeyboardButton(
                text="Новачок / хочу монтажити",
                url=f"https://t.me/{settings.bot_username}?start=installer_newbie",
            )
        ],
        [
            InlineKeyboardButton(
                text="Монтажник / хочу замовлення",
                url=f"https://t.me/{settings.bot_username}?start=installer_pro",
            )
        ],
        [InlineKeyboardButton(text="Калькулятор на сайті", url=settings.calculator_url)],
    ]
    if settings.client_group_url:
        rows.insert(2, [InlineKeyboardButton(text="Відкрита група консультацій", url=settings.client_group_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def phone_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Надіслати номер телефону", request_contact=True))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
