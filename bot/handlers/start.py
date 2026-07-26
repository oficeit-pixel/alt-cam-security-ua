from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.db.base import SessionLocal
from bot.db.models import User
from bot.db.requests import accept_terms, delete_user_personal_data, get_or_create_user
from bot.keyboards.common import accept_terms_keyboard, main_menu
from bot.middlewares.captcha import ask_captcha

router = Router(name="start")


async def route_start_intent(target, state: FSMContext, intent: str | None, *, edit: bool = False) -> bool:
    if intent in {"installer_newbie", "installer_pro"}:
        from bot.handlers.installer import start_installer_quiz

        track = "newbie" if intent == "installer_newbie" else "pro"
        await start_installer_quiz(target, state, track, edit=edit)
        return True

    if intent == "service":
        text = (
            "Відкрийте розділ «Виклик майстра / Сервіс».\n\n"
            "Бот уточнить тип несправності, бренд обладнання, опис проблеми і контакт для зв'язку."
        )
    elif intent == "client":
        text = (
            "Оберіть напрямок системи безпеки.\n\n"
            "Бот поставить кілька питань по об'єкту, UPS, кількості точок і підготує попередній розрахунок."
        )
    else:
        return False

    if edit:
        await target.edit_text(text, reply_markup=main_menu())
    else:
        await target.answer(text, reply_markup=main_menu())
    return True


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:
    intent = command.args
    if intent:
        await state.update_data(start_intent=intent)
    async with SessionLocal() as session:
        user = await get_or_create_user(
            session, telegram_id=message.from_user.id, full_name=message.from_user.full_name
        )
        await session.commit()
        if not user.accepted_terms:
            await ask_captcha(message, state)
            return
    if await route_start_intent(message, state, intent):
        return
    await message.answer(
        "Вітаю! Я офіційний бот ALT-CAM Security UA.\n\n"
        "Допоможу підібрати систему безпеки, оформити сервісну заявку "
        "або подати анкету монтажника.",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "terms:accept")
async def terms_accept(callback: CallbackQuery, state: FSMContext) -> None:
    async with SessionLocal() as session:
        await accept_terms(session, callback.from_user.id)
        await session.commit()
    data = await state.get_data()
    intent = data.get("start_intent")
    await state.clear()
    if await route_start_intent(callback.message, state, intent, edit=True):
        await callback.answer()
        return
    await callback.message.edit_text(
        "Дякуємо. Оферту та обробку персональних даних підтверджено.\n\n"
        "Оберіть потрібний розділ:",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "back:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Оберіть потрібний розділ:",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Оберіть напрямок у меню. Для розрахунку системи натисніть категорію, "
        "для ремонту - «Виклик майстра / Сервіс», для видалення даних - /delete_me.",
        reply_markup=main_menu(),
    )


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(
        f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
        f"ID цього чату: <code>{message.chat.id}</code>"
    )


@router.message(Command("delete_me"))
async def cmd_delete_me(message: Message) -> None:
    async with SessionLocal() as session:
        await delete_user_personal_data(session, message.from_user.id)
        await session.commit()
    await message.answer("Ваші персональні дані видалено або знеособлено.")


@router.message(Command("terms"))
async def cmd_terms(message: Message) -> None:
    await message.answer(
        "Ознайомтесь з Офертою та Політикою персональних даних.",
        reply_markup=accept_terms_keyboard(),
    )
