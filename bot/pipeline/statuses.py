"""Inquiry state machine.

Новая -> Взята в работу -> Наличие проверено -> Счёт/условия отправлены ->
Подтверждена клиентом -> Оплачена/НП -> Заказано у поставщика ->
Оплачено поставщику -> Отправлено (ТТН) -> Закрыта / Отказ
"""
from __future__ import annotations

STATUS_ORDER: tuple[str, ...] = (
    "new",
    "taken",
    "stock_checked",
    "offer_sent",
    "confirmed",
    "paid",
    "supplier_ordered",
    "supplier_paid",
    "shipped",
    "closed",
)
TERMINAL = {"closed", "rejected"}
STATUSES: dict[str, str] = {
    "new": "🆕 Нова",
    "taken": "👤 Взята в роботу",
    "stock_checked": "📦 Наявність перевірено",
    "offer_sent": "🧾 Рахунок/умови надіслано",
    "confirmed": "✅ Підтверджено клієнтом",
    "paid": "💳 Оплачено / НП",
    "supplier_ordered": "🏭 Замовлено у постачальника",
    "supplier_paid": "💸 Оплачено постачальнику",
    "shipped": "🚚 Відправлено (ТТН)",
    "closed": "🏁 Закрита",
    "rejected": "❌ Відмова",
}
# Statuses after which the client no longer waits for a sales answer.
CLOSEABLE_FROM = {"paid", "supplier_ordered", "supplier_paid", "shipped"}
# Web order (admin CRM) statuses synced from the pipeline; None = leave untouched.
WEB_ORDER_STATUS = {
    "taken": "clarification",
    "supplier_ordered": "ordered_from_supplier",
    "supplier_paid": "waiting_tracking",
    "shipped": "shipped",
    "closed": "completed",
    "rejected": "canceled",
}
PAYMENT_METHODS = {"prepay": "Передоплата", "cod": "Накладений платіж"}


def label(status: str) -> str:
    return STATUSES.get(status, status)


def can_transition(current: str, target: str) -> bool:
    """Forward moves (skips allowed), one step back for corrections, reject from any open status,
    reopen a rejected inquiry back to 'taken'."""
    if target not in STATUSES or current not in STATUSES or current == target:
        return False
    if current == "rejected":
        return target == "taken"
    if current == "closed":
        return False
    if target == "rejected":
        return True
    if target == "closed":
        return current in CLOSEABLE_FROM
    cur, tgt = STATUS_ORDER.index(current), STATUS_ORDER.index(target)
    return tgt > cur or tgt == cur - 1


def next_actions(current: str) -> list[str]:
    """Statuses offered as one-tap buttons for the owner (most likely next steps first)."""
    if current in TERMINAL:
        return ["taken"] if current == "rejected" else []
    idx = STATUS_ORDER.index(current)
    forward = [s for s in STATUS_ORDER[idx + 1: idx + 3] if s != "closed" or current in CLOSEABLE_FROM]
    if current in CLOSEABLE_FROM and "closed" not in forward:
        forward.append("closed")
    return forward + ["rejected"]
