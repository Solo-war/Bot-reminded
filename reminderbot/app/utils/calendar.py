from __future__ import annotations

from datetime import date, timedelta
from calendar import monthrange
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


from reminderbot.presentation.localization import Localizer

def calendar_keyboard(i18n: Localizer, locale: str, year: int, month: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Header with month navigation
    prev_year, prev_month = _shift_month(year, month, -1)
    next_year, next_month = _shift_month(year, month, 1)
    builder.button(text="◀️", callback_data=f"cal:nav:{prev_year:04d}-{prev_month:02d}")
    builder.button(text=f"{year:04d}-{month:02d}", callback_data="cal:noop")
    builder.button(text="▶️", callback_data=f"cal:nav:{next_year:04d}-{next_month:02d}")
    builder.adjust(3)

    # Weekday header (Mon-Sun)
    for wd in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        builder.button(text=wd, callback_data="cal:noop")
    builder.adjust(7)

    # Days
    first_wd = date(year, month, 1).weekday()  # Monday=0
    days_in_month = monthrange(year, month)[1]

    # Fill leading blanks
    for _ in range((first_wd + 0) % 7):
        builder.button(text=" ", callback_data="cal:noop")

    for day in range(1, days_in_month + 1):
        builder.button(text=f"{day:02d}", callback_data=f"cal:pick:{year:04d}-{month:02d}-{day:02d}")
    builder.adjust(7)

    return builder.as_markup()


def hours_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for h in range(0, 24):
        builder.button(text=f"{h:02d}", callback_data=f"time:hour:{h:02d}")
    builder.adjust(6)
    return builder.as_markup()


def minutes_keyboard(hour: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # common minute steps
    for m in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
        builder.button(text=f"{m:02d}", callback_data=f"time:min:{hour:02d}:{m:02d}")
    builder.adjust(6)
    # back
    builder.button(text="⬅️ Часы", callback_data="time:back_hours")
    builder.adjust(6)
    return builder.as_markup()


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    m = month + delta
    y = year + (m - 1) // 12
    m = ((m - 1) % 12) + 1
    return y, m

