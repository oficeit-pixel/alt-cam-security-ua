from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.config import get_settings
from bot.db.models import InstallerProfile, User, UserRole
from bot.db.requests import get_or_create_user, upsert_installer_profile
from bot.keyboards.common import (
    admin_installer_keyboard,
    back_keyboard,
    installer_test_keyboard,
    installer_track_keyboard,
)
from bot.states.states import InstallerOnboardingSG

router = Router(name="installer")

NEWBIE_QUESTIONS = [
    {
        "text": "Який мінімальний інструмент потрібен для акуратного монтажу камери на об'єкті?",
        "options": ["Перфоратор, викрутки, тестер, обжимка RJ-45", "Тільки телефон і ізолента", "Тільки драбина"],
        "answer": 0,
    },
    {
        "text": "Що треба зробити перед свердлінням стіни на об'єкті клієнта?",
        "options": ["Уточнити трасу кабелів/труб і погодити місце", "Свердлити одразу", "Поставити камеру де зручніше майстру"],
        "answer": 0,
    },
    {
        "text": "Як правильно завершувати просту сервісну роботу?",
        "options": ["Перевірити роботу, зробити фото, передати результат менеджеру", "Поїхати без перевірки", "Написати тільки суму"],
        "answer": 0,
    },
]

PRO_QUESTIONS = [
    {
        "text": "Який кабель коректніше використовувати для PoE на вулиці?",
        "options": ["FTP мідь для зовнішніх робіт", "UTP омеднений CCA", "Будь-який телефонний кабель"],
        "answer": 0,
    },
    {
        "text": "Стандартна рекомендована відстань Ethernet/PoE без додаткового обладнання?",
        "options": ["100 м", "300 м", "500 м"],
        "answer": 0,
    },
    {
        "text": "Для електрозамка з імпульсним живленням часто використовують:",
        "options": ["БУЗ/контролер живлення", "Тільки скрутку дротів", "HDMI-кабель"],
        "answer": 0,
    },
    {
        "text": "Як краще захистити відеореєстратор і PoE-комутатор від короткого відключення живлення?",
        "options": ["Підібрати UPS з запасом по потужності та часу", "Підключити напряму без резерву", "Поставити будь-який павербанк"],
        "answer": 0,
    },
]

QUESTION_SETS = {
    "newbie": {
        "label": "новачка",
        "questions": NEWBIE_QUESTIONS,
        "pass_score": 2,
        "intro": (
            "Анкета новачка ALT-CAM.\n\n"
            "Мета — зрозуміти, чи можна давати вам прості сервісні або допоміжні роботи "
            "та з чого почати навчання."
        ),
    },
    "pro": {
        "label": "монтажника",
        "questions": PRO_QUESTIONS,
        "pass_score": 4,
        "intro": (
            "Анкета монтажника ALT-CAM.\n\n"
            "Спочатку короткий професійний тест для доступу до закритої групи замовлень."
        ),
    },
}


async def start_installer_quiz(target, state: FSMContext, track: str, *, edit: bool = False) -> None:
    quiz = QUESTION_SETS[track]
    questions = quiz["questions"]
    await state.set_state(InstallerOnboardingSG.prof_quiz)
    await state.update_data(question=0, score=0, installer_track=track)
    q = questions[0]
    await state.update_data(answers={})
    text = f"{quiz['intro']}\n\nПитання 1/{len(questions)}:\n\n{q['text']}"
    if edit:
        await target.edit_text(text, reply_markup=installer_test_keyboard(0, q["options"]))
    else:
        await target.answer(text, reply_markup=installer_test_keyboard(0, q["options"]))


@router.callback_query(F.data == "installer:start")
async def installer_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Оберіть ваш рівень, щоб бот поставив правильні питання.\n\n"
        "Новачкам — питання по інструменту, акуратності та готовності працювати по чек-листу.\n"
        "Монтажникам — професійний тест, документи і портфоліо.",
        reply_markup=installer_track_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"installer:track:newbie", "installer:track:pro"}))
async def installer_track_start(callback: CallbackQuery, state: FSMContext) -> None:
    track = callback.data.rsplit(":", 1)[1]
    await start_installer_quiz(callback.message, state, track, edit=True)
    await callback.answer()


@router.callback_query(F.data == "installer:back:track")
async def installer_back_to_track(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Оберіть ваш рівень, щоб бот поставив правильні питання.\n\n"
        "Новачкам — питання по інструменту, акуратності та готовності працювати по чек-листу.\n"
        "Монтажникам — професійний тест, документи і портфоліо.",
        reply_markup=installer_track_keyboard(),
    )
    await callback.answer()


@router.message(F.text == "/installer")
async def installer_command(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Оберіть ваш рівень, щоб бот поставив правильні питання.",
        reply_markup=installer_track_keyboard(),
    )


@router.callback_query(InstallerOnboardingSG.prof_quiz, F.data.startswith("test:"))
async def test_answer(callback: CallbackQuery, state: FSMContext, session) -> None:
    _, question_raw, answer_raw = callback.data.split(":")
    question_index = int(question_raw)
    answer_index = int(answer_raw)
    data = await state.get_data()
    track = data.get("installer_track", "pro")
    quiz = QUESTION_SETS.get(track, QUESTION_SETS["pro"])
    questions = quiz["questions"]
    answers = dict(data.get("answers", {}))
    answers[str(question_index)] = answer_index

    next_index = question_index + 1
    if next_index < len(questions):
        await state.update_data(question=next_index, answers=answers)
        q = questions[next_index]
        await callback.message.edit_text(
            f"Питання {next_index + 1}/{len(questions)}:\n\n{q['text']}",
            reply_markup=installer_test_keyboard(next_index, q["options"]),
        )
        await callback.answer()
        return

    score = sum(
        1
        for idx, question in enumerate(questions)
        if int(answers.get(str(idx), -1)) == question["answer"]
    )
    if score < quiz["pass_score"]:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            role=UserRole.installer,
        )
        await upsert_installer_profile(
            session, user=user, fop_code=None, test_score=score, portfolio_photos=[]
        )
        await session.commit()
        await state.clear()
        await callback.message.edit_text(
            "Тест поки не пройдено.\n\n"
            "Адміністратор може підказати, що підтягнути, і коли краще подати анкету повторно."
        )
        await callback.answer()
        return

    await state.update_data(score=score, answers=answers, portfolio_photos=[])
    await state.set_state(InstallerOnboardingSG.docs_upload)
    await callback.message.edit_text(
        "Тест пройдено.\n\n"
        "Надішліть ФОП/ЄДРПОУ або коротко напишіть документ/формат співпраці. "
        "Якщо поки немає, напишіть «без ФОП».",
    )
    await callback.answer()


@router.callback_query(F.data == "installer:back:docs")
async def installer_back_to_docs(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(InstallerOnboardingSG.docs_upload)
    await callback.message.edit_text(
        "Надішліть ФОП/ЄДРПОУ або коротко напишіть документ/формат співпраці. "
        "Якщо поки немає, напишіть «без ФОП».",
    )
    await callback.answer()


@router.message(InstallerOnboardingSG.docs_upload)
async def docs_upload(message: Message, state: FSMContext) -> None:
    await state.update_data(fop_code=message.text.strip())
    await state.set_state(InstallerOnboardingSG.portfolio_upload)
    await message.answer(
        "Надішліть 3 фото виконаних робіт: шафа/трасса/камера або домофон.\n"
        "Коли завантажите фото, напишіть «готово».",
        reply_markup=back_keyboard("installer:back:docs"),
    )


@router.message(InstallerOnboardingSG.portfolio_upload, F.photo)
async def portfolio_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data.get("portfolio_photos", [])
    if len(photos) >= 3:
        await message.answer("Вже є 3 фото. Напишіть «готово».")
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(portfolio_photos=photos)
    await message.answer(
        f"Фото додано ({len(photos)}/3).",
        reply_markup=back_keyboard("installer:back:docs"),
    )


@router.message(InstallerOnboardingSG.portfolio_upload, F.text.casefold() == "готово")
async def portfolio_done(message: Message, state: FSMContext, session) -> None:
    settings = get_settings()
    data = await state.get_data()
    photos = data.get("portfolio_photos", [])
    if len(photos) < 3:
        await message.answer("Потрібно мінімум 3 фото робіт.")
        return
    user = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        role=UserRole.installer,
    )
    profile = await upsert_installer_profile(
        session,
        user=user,
        fop_code=data.get("fop_code"),
        test_score=int(data.get("score", 0)),
        portfolio_photos=photos,
    )
    await session.commit()
    await state.set_state(InstallerOnboardingSG.wait_approval)
    await message.bot.send_message(
        settings.admin_chat_id,
        "Нова анкета монтажника\n\n"
        f"Ім'я: <b>{message.from_user.full_name}</b>\n"
        f"Telegram ID: <code>{message.from_user.id}</code>\n"
        f"Рівень: <b>{data.get('installer_track', 'pro')}</b>\n"
        f"ФОП/документ: <b>{profile.fop_code}</b>\n"
        f"Тест: <b>{profile.test_score}</b>",
        reply_markup=admin_installer_keyboard(user.id),
    )
    for file_id in photos:
        await message.bot.send_photo(settings.admin_chat_id, file_id)
    await message.answer("Анкету передано адміністратору. Очікуйте рішення.")


@router.callback_query(F.data.startswith("installer:approve:"))
async def approve_installer(callback: CallbackQuery, session) -> None:
    settings = get_settings()
    installer_user_id = int(callback.data.rsplit(":", 1)[1])
    profile = await session.scalar(
        select(InstallerProfile).where(InstallerProfile.user_id == installer_user_id)
    )
    user = await session.get(User, installer_user_id)
    if not profile or not user:
        await callback.answer("Анкету не знайдено.", show_alert=True)
        return
    profile.is_verified = True
    profile.verified_at = datetime.now(timezone.utc)
    await session.commit()
    invite = await callback.bot.create_chat_invite_link(
        settings.installer_group_id,
        expire_date=datetime.now(timezone.utc) + timedelta(hours=24),
        member_limit=1,
        creates_join_request=False,
    )
    await callback.bot.send_message(
        user.telegram_id,
        "Вас одобрено як монтажника ALT-CAM.\n\n"
        f"Одноразове посилання в закриту групу: {invite.invite_link}"
    )
    await callback.message.edit_text("Монтажника одобрено. Інвайт надіслано.")
    await callback.answer()


@router.callback_query(F.data.startswith("installer:reject:"))
async def reject_installer(callback: CallbackQuery, session) -> None:
    installer_user_id = int(callback.data.rsplit(":", 1)[1])
    user = await session.get(User, installer_user_id)
    if user:
        await callback.bot.send_message(
            user.telegram_id,
            "Анкету монтажника поки відхилено. Деталі можна уточнити в адміністратора.",
        )
    await callback.message.edit_text("Анкету відхилено.")
    await callback.answer()
