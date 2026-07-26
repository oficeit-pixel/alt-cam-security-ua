from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.db.models import Order, OrderBid, User
from bot.db.requests import accept_bid, create_bid, get_or_create_user
from bot.keyboards.common import client_bid_keyboard
from bot.states.states import AuctionBidSG

router = Router(name="auction")


@router.callback_query(F.data.startswith("bid:start:"))
async def bid_start(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.rsplit(":", 1)[1])
    await state.set_state(AuctionBidSG.price_input)
    await state.update_data(order_id=order_id)
    await callback.message.answer("Вкажіть вашу ціну за виконання робіт у гривнях.")
    await callback.answer()


@router.message(AuctionBidSG.price_input)
async def bid_price(message: Message, state: FSMContext) -> None:
    raw = message.text.replace(" ", "").replace("грн", "")
    if not raw.isdigit():
        await message.answer("Введіть тільки суму цифрами, наприклад 6500.")
        return
    await state.update_data(price_offer=int(raw))
    await state.set_state(AuctionBidSG.comment_input)
    await message.answer("Додайте короткий коментар: коли можете виконати, що входить у ціну.")


@router.message(AuctionBidSG.comment_input)
async def bid_comment(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    installer = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
    )
    bid = await create_bid(
        session,
        order_id=data["order_id"],
        installer=installer,
        price_offer=data["price_offer"],
        comment=message.text.strip(),
    )
    order = await session.get(Order, data["order_id"])
    client = await session.get(User, order.client_id) if order else None
    await session.commit()
    if client:
        await message.bot.send_message(
            client.telegram_id,
            "Монтажник відгукнувся на ваше замовлення\n\n"
            "Майстер: перевірений монтажник ALT-CAM\n"
            f"Пропозиція: <b>{bid.price_offer:,} ₴</b>\n"
            f"Коментар: {bid.comment}\n\n"
            "Контакти відкриються після вибору майстра.",
            reply_markup=client_bid_keyboard(bid.id),
        )
    await state.clear()
    await message.answer("Ваш відгук передано клієнту.")


@router.callback_query(F.data.startswith("bid:accept:"))
async def bid_accept(callback: CallbackQuery, session) -> None:
    bid_id = int(callback.data.rsplit(":", 1)[1])
    bid = await accept_bid(session, bid_id)
    if not bid:
        await callback.answer("Відгук не знайдено.", show_alert=True)
        return
    order = await session.get(Order, bid.order_id)
    client = await session.get(User, order.client_id) if order else None
    installer = await session.get(User, bid.installer_id)
    await session.commit()
    if client and installer:
        await callback.bot.send_message(
            installer.telegram_id,
            "Клієнт обрав вашу пропозицію.\n\n"
            f"Клієнт: {client.full_name or 'не вказано'}\n"
            f"Telegram ID клієнта: <code>{client.telegram_id}</code>",
        )
        await callback.message.edit_text(
            "Майстра обрано. Контакти передано сторонам, заявка в роботі."
        )
    await callback.answer()
