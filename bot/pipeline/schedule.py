"""Working hours helpers (business timezone, default Europe/Kyiv)."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from bot.config import get_settings


def _tz() -> ZoneInfo:
    return ZoneInfo(get_settings().business_timezone)


def _parse_hhmm(value: str) -> time:
    hours, minutes = value.strip().split(":")
    return time(int(hours), int(minutes))


def work_window() -> tuple[time, time]:
    start, _, end = get_settings().work_hours.partition("-")
    return _parse_hhmm(start), _parse_hhmm(end)


def work_days() -> set[int]:
    return {int(item) for item in get_settings().work_days.split(",") if item.strip().isdigit()}


def local(now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(_tz())


def is_working_time(now: datetime | None = None) -> bool:
    current = local(now)
    start, end = work_window()
    return current.weekday() in work_days() and start <= current.time() < end


def next_work_start(now: datetime | None = None) -> datetime:
    current = local(now)
    start, _ = work_window()
    for offset in range(0, 8):
        day = (current + timedelta(days=offset)).date()
        candidate = datetime.combine(day, start, tzinfo=current.tzinfo)
        if day.weekday() in work_days() and candidate > current:
            return candidate
    return current + timedelta(days=1)


def before_ship_cutoff(now: datetime | None = None) -> bool:
    current = local(now)
    return current.weekday() in work_days() and current.time() < _parse_hhmm(get_settings().ship_cutoff)


DAY_NAMES = ["понеділок", "вівторок", "середу", "четвер", "п’ятницю", "суботу", "неділю"]


def eta_text(now: datetime | None = None) -> str:
    """Human expected answer time for the client auto-reply."""
    settings = get_settings()
    if is_working_time(now):
        return settings.reply_eta_text
    start = next_work_start(now)
    current = local(now)
    if start.date() == current.date():
        return f"сьогодні після {start:%H:%M}"
    if start.date() == (current + timedelta(days=1)).date():
        return f"завтра після {start:%H:%M}"
    return f"у {DAY_NAMES[start.weekday()]} після {start:%H:%M}"
