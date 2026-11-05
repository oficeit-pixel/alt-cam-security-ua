"""Background jobs: escalating reminders, 24h client follow-up, Nova Poshta tracking."""
from __future__ import annotations

import logging

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.integrations import nova_poshta_tracking as np
from bot.pipeline import contacts, delivery, notify, schedule, service, texts

logger = logging.getLogger("altcam.pipeline.jobs")


async def run_reminders(bot, now=None) -> int:
    settings = get_settings()
    if bot is None or not schedule.is_working_time(now):
        return 0
    await contacts.safe_reload()  # pick up owner / second contact registered via /start in another process
    sent = 0
    async with SessionLocal() as session:
        repaired = await service.repair_stale_sla(session)
        await session.commit()
        if repaired:
            logger.info("Repaired %s acknowledged SLA waits", repaired)
        due = await service.due_reminders(session, settings.reminder_thresholds, now)
        for inquiry, level in due:
            if not await service.claim_reminder(session, inquiry.id, level):
                continue
            await session.commit()
            waited = int(((now or service.utcnow()) - inquiry.awaiting_since).total_seconds() // 60)
            header = f"{notify.LEVEL_LABELS.get(level, '⏰')} — без відповіді {waited} хв"
            if not inquiry.client_chat_id and inquiry.phone:
                header += f"\n📞 Клієнта немає в боті — зателефонуйте: <code>{inquiry.phone}</code>"
            sent += await notify.send_owner_card(bot, session, inquiry, header=header, level=level)
            await session.commit()
    return sent


async def run_followups(bot, now=None) -> int:
    settings = get_settings()
    if bot is None or not schedule.is_working_time(now):
        return 0
    sent = 0
    async with SessionLocal() as session:
        for inquiry in await service.due_followups(session, settings.followup_hours, now):
            if not await service.claim_followup(session, inquiry.id, now):
                continue
            await session.commit()
            if inquiry.client_chat_id and not delivery.is_business(inquiry):
                try:
                    await bot.send_message(inquiry.client_chat_id, texts.followup_text(inquiry.id),
                                           reply_markup=notify.client_confirm_keyboard(inquiry.id))
                    await service.add_event(session, inquiry.id, "followup", "system", "client follow-up sent")
                    sent += 1
                except Exception as exc:
                    logger.warning("followup_failed inquiry=%s (%s)", inquiry.id, type(exc).__name__)
            header = f"🔔 Клієнт мовчить {settings.followup_hours} год після пропозиції" + (
                " — напишіть клієнту в особистому чаті" if delivery.is_business(inquiry)
                else " — бот надіслав нагадування" if inquiry.client_chat_id else " — зателефонуйте")
            await notify.send_owner_card(bot, session, inquiry, header=header, level=1)
            await session.commit()
    return sent


async def run_np_tracking(bot) -> int:
    settings = get_settings()
    if bot is None or not settings.nova_poshta_api_key:
        return 0
    changed = 0
    async with SessionLocal() as session:
        inquiries = await service.shipped_with_ttn(session)
        if not inquiries:
            return 0
        try:
            statuses = await np.fetch_statuses([(i.ttn, i.phone) for i in inquiries])
        except Exception as exc:
            logger.warning("np_tracking_failed (%s)", type(exc).__name__)
            return 0
        for inquiry in inquiries:
            info = statuses.get(inquiry.ttn or "")
            if not info or info["code"] == (inquiry.np_status_code or ""):
                continue
            previous = np.classify(inquiry.np_status_code)
            inquiry.np_status_code = info["code"][:8]
            kind = np.classify(info["code"])
            await service.add_event(session, inquiry.id, "np_status", "system", f"{info['code']}: {info['status']}")
            if kind == "arrived" and previous != "arrived" and delivery.is_business(inquiry):
                await notify.send_owner_card(bot, session, inquiry, header="📦 Посилка прибула — повідомте клієнта", level=1)
            elif kind == "arrived" and previous != "arrived" and inquiry.client_chat_id:
                try:
                    await bot.send_message(inquiry.client_chat_id, texts.arrived_text(inquiry.ttn))
                except Exception as exc:
                    logger.warning("np_arrived_notify_failed inquiry=%s (%s)", inquiry.id, type(exc).__name__)
            elif kind == "received":
                await service.transition(session, inquiry, "closed", actor="nova_poshta", note=f"НП: {info['status']}"[:200])
            elif kind == "problem":
                await notify.send_owner_card(bot, session, inquiry, header=f"📦❗ Нова пошта: {info['status']}", level=2)
            changed += 1
        await session.commit()
    return changed


def setup_pipeline_jobs(scheduler, bot) -> bool:
    settings = get_settings()
    if not (settings.pipeline_enabled and settings.scheduler_active and bot is not None):
        return False
    scheduler.add_job(run_reminders, "interval", minutes=1, args=[bot], id="pipeline_reminders",
                      max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(run_followups, "interval", minutes=30, args=[bot], id="pipeline_followups",
                      max_instances=1, coalesce=True, replace_existing=True)
    if settings.nova_poshta_api_key:
        scheduler.add_job(run_np_tracking, "interval", minutes=max(15, settings.np_tracking_interval_minutes), args=[bot],
                          id="pipeline_np_tracking", max_instances=1, coalesce=True, replace_existing=True)
    else:
        logger.info("Nova Poshta tracking disabled: NOVA_POSHTA_API_KEY is not set (TTN is still sent to the client)")
    return True
