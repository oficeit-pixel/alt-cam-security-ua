from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import group_guide_keyboard, guide_private_keyboard

router = Router(name="group_guide")


WELCOME_TEXT = (
    "Вітаємо в ALT-CAM Security UA.\n\n"
    "Я допоможу швидко обрати правильний напрямок. Якщо ви клієнт — підкажу по системі "
    "та заявці. Якщо потрібен сервіс — направлю до майстра. Якщо хочете працювати з нами "
    "як монтажник — спочатку визначимо ваш рівень.\n\n"
    "Оберіть, що вам потрібно:"
)


@router.message(F.new_chat_members)
async def welcome_new_members(message: Message) -> None:
    names = ", ".join(member.full_name for member in message.new_chat_members)
    await message.answer(
        f"{names}, раді бачити вас у групі.\n\n{WELCOME_TEXT}",
        reply_markup=group_guide_keyboard(),
    )


@router.message(F.text.in_({"/guide", "/menu", "меню", "Меню"}))
async def show_group_guide(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=group_guide_keyboard())


@router.callback_query(F.data == "guide:menu")
async def guide_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=group_guide_keyboard())
    await callback.answer()


@router.callback_query(F.data == "guide:client")
async def guide_client(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Для клієнта найкращий шлях такий:\n\n"
        "1. Відкрити бота.\n"
        "2. Пройти короткий квиз: об'єкт, кількість камер/точок, UPS, фото.\n"
        "3. Отримати попередній розрахунок і передати заявку менеджеру.\n\n"
        "Якщо хочете просто оцінити бюджет — відкрийте калькулятор на сайті.",
        reply_markup=guide_private_keyboard("client"),
    )
    await callback.answer()


@router.callback_query(F.data == "guide:service")
async def guide_service(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Якщо вже є обладнання і потрібна допомога:\n\n"
        "• не працюють камери;\n"
        "• збився доступ Hik-Connect/DMSS;\n"
        "• потрібно замінити диск;\n"
        "• є проблема з UPS або живленням.\n\n"
        "Відкрийте бота і оберіть «Виклик майстра / Сервіс».",
        reply_markup=guide_private_keyboard("service"),
    )
    await callback.answer()


@router.callback_query(F.data == "guide:installer_newbie")
async def guide_installer_newbie(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Напрямок для новачків.\n\n"
        "Ми перевіримо базові речі:\n"
        "• чи є ручний інструмент і перфоратор;\n"
        "• чи розумієте, як прокладати кабель без пошкоджень;\n"
        "• чи готові працювати по чек-листу, фотофіксації і правилах об'єкта.\n\n"
        "Після анкети адміністратор вирішить, які прості сервісні або допоміжні задачі можна давати.",
        reply_markup=guide_private_keyboard("installer_newbie"),
    )
    await callback.answer()


@router.callback_query(F.data == "guide:installer_pro")
async def guide_installer_pro(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Напрямок для досвідчених монтажників.\n\n"
        "Потрібно:\n"
        "1. Пройти професійний тест по PoE, UPS, домофонії та СКУД.\n"
        "2. Вказати ФОП/формат співпраці.\n"
        "3. Надіслати 3 фото виконаних робіт.\n"
        "4. Дочекатися одобрення адміністратора.\n\n"
        "Після одобрення бот створить одноразове посилання в закриту групу замовлень.",
        reply_markup=guide_private_keyboard("installer_pro"),
    )
    await callback.answer()
