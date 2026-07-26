from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards.common import accept_terms_keyboard, captcha_keyboard
from bot.states.states import CaptchaState, TermsState

router = Router(name="captcha")


async def ask_captcha(message, state: FSMContext) -> None:
    await state.set_state(CaptchaState.waiting_for_captcha)
    await message.answer(
        "Щоб захистити бот від спаму, оберіть відеокамеру:",
        reply_markup=captcha_keyboard(),
    )


@router.callback_query(CaptchaState.waiting_for_captcha)
async def captcha_answer(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data != "captcha:camera":
        await callback.answer("Спробуйте ще раз.", show_alert=True)
        await callback.message.edit_text(
            "Оберіть правильний символ: відеокамеру.",
            reply_markup=captcha_keyboard(),
        )
        return
    await state.set_state(TermsState.waiting_for_accept)
    await callback.message.edit_text(
        "Дякуємо. Тепер підтвердьте згоду з Офертою та обробкою персональних даних.",
        reply_markup=accept_terms_keyboard(),
    )
    await callback.answer()
