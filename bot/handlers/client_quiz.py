from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import get_settings
from bot.db.models import User
from bot.db.requests import create_order, get_or_create_user, publish_order
from bot.keyboards.common import (
    object_type_keyboard,
    order_confirm_keyboard,
    photo_upload_keyboard,
    points_count_keyboard,
    yes_no_keyboard,
)
from bot.states.states import ClientQuizSG
from bot.utils.google_drive import get_order_card_file_id

router = Router(name="client_quiz")

CATEGORY_LABELS = {
    "cctv": "Відеоспостереження",
    "intercom": "Домофонія та СКУД",
    "ajax": "Сигналізація Ajax",
    "ups": "UPS та резервне живлення",
}


def estimate_price(category: str, points_count: str, need_ups: bool) -> tuple[int, int]:
    points = 2
    if points_count.startswith("3-4"):
        points = 4
    elif points_count.startswith("5-8"):
        points = 8
    elif points_count.startswith("9+"):
        points = 12
    elif points_count == "Не знаю":
        points = 4

    base_by_category = {
        "cctv": 4200,
        "intercom": 5200,
        "ajax": 3800,
        "ups": 3000,
    }
    base = base_by_category.get(category, 4200)
    equipment = points * base + 4500
    work = points * 1800 + 2500
    ups = 6500 if need_ups else 0
    total = equipment + work + ups
    return round(total * 0.9 / 500) * 500, round(total * 1.15 / 500) * 500


@router.callback_query(F.data.startswith("category:"))
async def select_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split(":", 1)[1]
    await state.set_state(ClientQuizSG.object_type)
    await state.update_data(category=category, category_label=CATEGORY_LABELS[category])
    await callback.message.edit_text(
        f"Обрано: <b>{CATEGORY_LABELS[category]}</b>\n\n"
        "Який тип об'єкта потрібно захистити?",
        reply_markup=object_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back:client:object")
async def back_to_object_type(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    category_label = data.get("category_label", "обраний напрямок")
    await state.set_state(ClientQuizSG.object_type)
    await callback.message.edit_text(
        f"Обрано: <b>{category_label}</b>\n\n"
        "Який тип об'єкта потрібно захистити?",
        reply_markup=object_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(ClientQuizSG.object_type, F.data.startswith("object:"))
async def select_object(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(object_type=callback.data.split(":", 1)[1])
    await state.set_state(ClientQuizSG.points_count)
    await callback.message.edit_text(
        "Скільки точок/камер/пристроїв орієнтовно потрібно?",
        reply_markup=points_count_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back:client:points")
async def back_to_points_count(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ClientQuizSG.points_count)
    await callback.message.edit_text(
        "Скільки точок/камер/пристроїв орієнтовно потрібно?",
        reply_markup=points_count_keyboard(),
    )
    await callback.answer()


@router.callback_query(ClientQuizSG.points_count, F.data.startswith("points:"))
async def select_points(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(points_count=callback.data.split(":", 1)[1])
    await state.set_state(ClientQuizSG.need_ups)
    await callback.message.edit_text(
        "Чи потрібне резервне живлення під час відключень світла?",
        reply_markup=yes_no_keyboard("ups"),
    )
    await callback.answer()


@router.callback_query(F.data == "back:client:ups")
async def back_to_ups(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ClientQuizSG.need_ups)
    await callback.message.edit_text(
        "Чи потрібне резервне живлення під час відключень світла?",
        reply_markup=yes_no_keyboard("ups"),
    )
    await callback.answer()


@router.callback_query(ClientQuizSG.need_ups, F.data.startswith("ups:"))
async def select_ups(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(require_ups=callback.data.endswith(":yes"), photos=[])
    await state.set_state(ClientQuizSG.photo_upload)
    await callback.message.edit_text(
        "Надішліть до 3 фото об'єкта: фасад, місце встановлення, щит/роутер або вхід.\n\n"
        "Коли фото додані, натисніть «Готово».",
        reply_markup=photo_upload_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back:client:photos")
async def back_to_photos(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ClientQuizSG.photo_upload)
    await callback.message.edit_text(
        "Надішліть до 3 фото об'єкта: фасад, місце встановлення, щит/роутер або вхід.\n\n"
        "Коли фото додані, натисніть «Готово».",
        reply_markup=photo_upload_keyboard(),
    )
    await callback.answer()


@router.message(ClientQuizSG.photo_upload, F.photo)
async def collect_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 3:
        await message.answer("Достатньо 3 фото. Натисніть «Готово».", reply_markup=photo_upload_keyboard())
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(
        f"Фото додано ({len(photos)}/3).",
        reply_markup=photo_upload_keyboard(),
    )


@router.callback_query(ClientQuizSG.photo_upload, F.data.in_({"photos:done", "photos:skip"}))
async def finish_photos(callback: CallbackQuery, state: FSMContext, session, db_user: User) -> None:
    data = await state.get_data()
    low, high = estimate_price(
        data["category"], data["points_count"], data.get("require_ups", False)
    )
    client = await get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
    )
    order = await create_order(
        session,
        client=client,
        category=data["category"],
        object_type=data["object_type"],
        points_count=data["points_count"],
        require_ups=data.get("require_ups", False),
        photos=data.get("photos", []),
        estimated_price_min=low,
        estimated_price_max=high,
    )
    await session.commit()
    await state.set_state(ClientQuizSG.confirm_order)
    await state.update_data(order_id=order.id)
    await callback.message.edit_text(
        "Попередній розрахунок ALT-CAM Security UA\n\n"
        f"Напрямок: <b>{data['category_label']}</b>\n"
        f"Об'єкт: <b>{data['object_type']}</b>\n"
        f"Кількість точок: <b>{data['points_count']}</b>\n"
        f"UPS: <b>{'потрібен' if data.get('require_ups') else 'не потрібен'}</b>\n\n"
        f"Орієнтовна вартість: <b>{low:,} - {high:,} ₴</b>\n\n"
        "Це не оферта. Точна ціна залежить від планування, кабелю, висоти монтажу, "
        "обладнання та доступу до об'єкта.",
        reply_markup=order_confirm_keyboard(order.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:publish:"))
async def publish_to_installers(callback: CallbackQuery, session) -> None:
    settings = get_settings()
    order_id = int(callback.data.rsplit(":", 1)[1])
    order = await publish_order(session, order_id)
    await session.commit()
    if not order:
        await callback.answer("Замовлення не знайдено.", show_alert=True)
        return
    from bot.keyboards.common import auction_order_keyboard

    await callback.bot.send_message(
        settings.installer_group_id,
        "Нове замовлення для монтажників\n\n"
        f"Категорія: <b>{order.category}</b>\n"
        f"Об'єкт: <b>{order.object_type}</b>\n"
        f"Кількість точок: <b>{order.points_count}</b>\n"
        f"UPS: <b>{'так' if order.require_ups else 'ні'}</b>\n"
        f"Оцінка: <b>{order.estimated_price_min:,} - {order.estimated_price_max:,} ₴</b>\n\n"
        "Контакти клієнта приховані до вибору майстра.",
        reply_markup=auction_order_keyboard(order.id),
    )
    await callback.message.answer("Замовлення опубліковано для перевірених монтажників.")
    await callback.answer()


@router.callback_query(F.data.startswith("drive:card:"))
async def send_drive_card(callback: CallbackQuery) -> None:
    file_id = await get_order_card_file_id(callback.data.rsplit(":", 1)[1])
    if file_id:
        await callback.message.answer_document(file_id)
    else:
        await callback.message.answer(
            "Картка з Google Drive ще не налаштована. Менеджер підготує її вручну."
        )
    await callback.answer()
