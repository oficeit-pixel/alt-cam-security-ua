from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from bot.db.base import SessionLocal
from bot.db.models import User
from bot.db.requests import get_or_create_user
from bot.keyboards.common import accept_terms_keyboard, captcha_keyboard
from bot.states.states import CaptchaState, TermsState

PUBLIC_COMMANDS = {"/start", "/help", "/delete_me"}
PUBLIC_CALLBACK_PREFIXES = ("captcha:", "terms:", "guide:")


class TermsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        text = event.text if isinstance(event, Message) else None
        callback_data = event.data if isinstance(event, CallbackQuery) else None
        if isinstance(event, Message) and event.new_chat_members:
            return await handler(event, data)
        if text in PUBLIC_COMMANDS or (
            callback_data and callback_data.startswith(PUBLIC_CALLBACK_PREFIXES)
        ):
            return await handler(event, data)

        state = data.get("state")
        current_state = await state.get_state() if state else None
        if current_state in {
            CaptchaState.waiting_for_captcha.state,
            TermsState.waiting_for_accept.state,
        }:
            return await handler(event, data)

        async with SessionLocal() as session:
            db_user = await get_or_create_user(
                session, telegram_id=user.id, full_name=user.full_name
            )
            await session.commit()
            data["session"] = session
            data["db_user"] = db_user
            accepted = await session.scalar(
                select(User.accepted_terms).where(User.telegram_id == user.id)
            )

        if not accepted:
            if state:
                await state.set_state(TermsState.waiting_for_accept)
            target = event.message if isinstance(event, CallbackQuery) else event
            await target.answer(
                "Перед продовженням потрібно погодитися з публічною офертою "
                "та обробкою персональних даних.",
                reply_markup=accept_terms_keyboard(),
            )
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None

        async with SessionLocal() as session:
            db_user = await get_or_create_user(
                session, telegram_id=user.id, full_name=user.full_name
            )
            data["session"] = session
            data["db_user"] = db_user
            result = await handler(event, data)
            await session.commit()
            return result
