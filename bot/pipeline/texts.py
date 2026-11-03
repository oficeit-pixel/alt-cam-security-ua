"""Client-facing texts (Ukrainian, as on alt-cam.net.ua). No prices or supplier data here.

Facts used: payment = prepayment or Nova Poshta cash-on-delivery, delivery by Nova Poshta paid by the
recipient, orders before SHIP_CUTOFF ship the same working day (owner's rules); return/warranty wording
follows delivery-and-returns.html. Every FAQ text can be overridden with FAQ_*_TEXT env vars.
"""
from __future__ import annotations

from html import escape

from bot.config import get_settings
from bot.pipeline import schedule

POLICY_URL = "https://alt-cam.net.ua/delivery-and-returns.html"


def auto_reply(inquiry_id: int, now=None) -> str:
    settings = get_settings()
    return (
        f"Вітаю! Ваш запит №{inquiry_id} отримано ✅\n\n"
        f"Менеджер відповість {schedule.eta_text(now)}. "
        "Поки чекаєте — напишіть модель або надішліть фото/посилання на товар, "
        "і вкажіть місто доставки: так ми швидше перевіримо наявність.\n\n"
        "Відповіді на часті питання — кнопками нижче."
        + ("" if settings.capture_before_terms is False else
           f"\n\n<i>Надсилаючи повідомлення, ви погоджуєтесь з <a href=\"{escape(settings.privacy_url)}\">Політикою ПД</a>.</i>")
    )


def faq_payment() -> str:
    settings = get_settings()
    return settings.faq_payment_text or (
        "<b>Оплата</b>\n\n"
        "• Передоплата на рахунок продавця — реквізити й остаточну суму надсилаємо після перевірки наявності.\n"
        "• Накладений платіж Новою поштою — оплата під час отримання у відділенні.\n\n"
        "Комісію за накладений платіж стягує Нова пошта за своїми тарифами. "
        "До оплати ви погоджуєте продавця, ціну та умови."
    )


def faq_delivery() -> str:
    settings = get_settings()
    return settings.faq_delivery_text or (
        "<b>Доставка</b>\n\n"
        "• Нова пошта: відділення, поштомат або кур’єр.\n"
        "• Доставку оплачує отримувач за тарифами перевізника.\n"
        f"• Замовлення, підтверджені до {settings.ship_cutoff} робочого дня, відправляємо того ж дня, "
        "якщо товар є на складі.\n"
        "• Після відправлення надішлемо номер ТТН сюди в Telegram.\n\n"
        f"Детальніше: {POLICY_URL}"
    )


def faq_warranty() -> str:
    settings = get_settings()
    return settings.faq_warranty_text or (
        "<b>Гарантія та повернення</b>\n\n"
        "• Гарантію надає продавець, зазначений у документах замовлення, на умовах виробника; "
        "строк для конкретної моделі повідомимо разом з рахунком.\n"
        "• Обмін/повернення товару належної якості — протягом 14 днів у випадках, передбачених законом.\n"
        "• При отриманні перевірте упаковку й комплектність у відділенні.\n\n"
        f"Детальніше: {POLICY_URL}"
    )


def faq_human() -> str:
    return "Покликав менеджера 🙋 Він отримав сповіщення й відповість якнайшвидше."


# Owner one-tap templated replies to the client. Keys are used in callback data (keep short).
TEMPLATES: dict[str, tuple[str, str]] = {
    "chk": ("🔎 Перевіряю наявність",
            "Дякую за запит! Перевіряю наявність у постачальника й повернусь з відповіддю найближчим часом."),
    "yes": ("✅ Є в наявності",
            "Гарна новина: товар є в наявності ✅ Підготую рахунок і умови доставки. "
            "Підкажіть, будь ласка: місто та відділення/поштомат Нової пошти, ПІБ і телефон отримувача, "
            "і як зручніше оплатити — передоплата чи накладений платіж?"),
    "no": ("⛔ Немає — аналог",
           "На жаль, цієї позиції зараз немає в наявності. Можу підібрати аналог з такими ж характеристиками — підготувати варіанти?"),
    "pay": ("💳 Умови оплати", None),
    "dlv": ("🚚 Умови доставки", None),
    "cnf": ("📝 Прошу підтвердити", "Перевірте, будь ласка, склад, суму та умови доставки вище й підтвердіть замовлення кнопкою нижче 👇"),
    "thx": ("🙏 Оплату отримано", "Оплату отримано, дякуємо! Передаємо замовлення на відправку — номер ТТН надішлемо сюди."),
}


def template_text(key: str) -> str | None:
    if key == "pay":
        return faq_payment()
    if key == "dlv":
        return faq_delivery()
    item = TEMPLATES.get(key)
    return item[1] if item else None


def taken_text(inquiry_id: int) -> str:
    return f"Ваш запит №{inquiry_id} взято в роботу 👤 Менеджер уже перевіряє деталі й скоро напише."


def shipped_text(ttn: str) -> str:
    return (
        f"Ваше замовлення відправлено 🚚\nНомер ТТН Нової пошти: <code>{escape(ttn)}</code>\n"
        f"Відстежити: https://novaposhta.ua/tracking/?cargo_number={escape(ttn)}"
    )


def arrived_text(ttn: str) -> str:
    return f"Посилка <code>{escape(ttn)}</code> прибула у відділення/поштомат Нової пошти 📬 Можна забирати!"


def followup_text(inquiry_id: int) -> str:
    return (
        f"Вітаю! Нагадую про ваш запит №{inquiry_id}. Чи актуальне замовлення? "
        "Якщо залишились питання щодо оплати чи доставки — натисніть кнопку нижче, і менеджер одразу відповість."
    )


def site_order_bound_text(order_number: str) -> str:
    return (
        f"Замовлення <b>{escape(order_number)}</b> прив’язано до цього чату ✅\n"
        "Сюди надійдуть підтвердження, рахунок і номер ТТН. Якщо є питання — просто напишіть їх тут."
    )
