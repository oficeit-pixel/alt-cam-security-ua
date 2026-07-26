from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import get_settings
from bot.keyboards.common import back_keyboard, service_fault_keyboard
from bot.states.states import ServiceSG

router = Router(name="service")


@router.callback_query(F.data == "service:start")
async def service_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ServiceSG.fault_type)
    await callback.message.edit_text(
        "Оберіть тип проблеми:", reply_markup=service_fault_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back:service:fault")
async def back_to_service_fault(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ServiceSG.fault_type)
    await callback.message.edit_text(
        "Оберіть тип проблеми:", reply_markup=service_fault_keyboard()
    )
    await callback.answer()


@router.callback_query(ServiceSG.fault_type, F.data.startswith("fault:"))
async def service_fault(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(fault_type=callback.data.split(":", 1)[1])
    await state.set_state(ServiceSG.brand)
    await callback.message.edit_text(
        "Вкажіть бренд обладнання: Hikvision, Dahua, Ajax, IMOU, інший.",
        reply_markup=back_keyboard("back:service:fault"),
    )
    await callback.answer()


@router.callback_query(F.data == "back:service:brand")
async def back_to_service_brand(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ServiceSG.brand)
    await callback.message.edit_text(
        "Вкажіть бренд обладнання: Hikvision, Dahua, Ajax, IMOU, інший.",
        reply_markup=back_keyboard("back:service:fault"),
    )
    await callback.answer()


@router.message(ServiceSG.brand)
async def service_brand(message: Message, state: FSMContext) -> None:
    await state.update_data(brand=message.text.strip())
    await state.set_state(ServiceSG.problem_desc)
    await message.answer(
        "Опишіть проблему коротко: що сталося, коли почалося, що вже пробували.",
        reply_markup=back_keyboard("back:service:brand"),
    )


@router.message(ServiceSG.problem_desc)
async def service_problem(message: Message, state: FSMContext) -> None:
    await state.update_data(problem_desc=message.text.strip())
    await state.set_state(ServiceSG.contact_info)
    await message.answer(
        "Залиште контакт для зв'язку: телефон або Telegram.",
        reply_markup=back_keyboard("back:service:problem"),
    )


@router.callback_query(F.data == "back:service:problem")
async def back_to_service_problem(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ServiceSG.problem_desc)
    await callback.message.edit_text(
        "Опишіть проблему коротко: що сталося, коли почалося, що вже пробували.",
        reply_markup=back_keyboard("back:service:brand"),
    )
    await callback.answer()


@router.message(ServiceSG.contact_info)
async def service_contact(message: Message, state: FSMContext) -> None:
    settings = get_settings()
    data = await state.get_data()
    await message.bot.send_message(
        settings.admin_chat_id,
        "Сервісна заявка\n\n"
        f"Проблема: <b>{data['fault_type']}</b>\n"
        f"Бренд: <b>{data['brand']}</b>\n"
        f"Опис: {data['problem_desc']}\n"
        f"Контакт: <code>{message.text.strip()}</code>\n"
        f"Клієнт Telegram ID: <code>{message.from_user.id}</code>",
    )
    await state.clear()
    await message.answer("Заявку передано дежурному інженеру. Менеджер зв'яжеться з вами.")
