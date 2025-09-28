from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CreateReminderStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time_hour = State()
    waiting_for_time_minute = State()
    waiting_for_repeat = State()


class SnoozeReminderStates(StatesGroup):
    waiting_for_minutes = State()


class QuietHoursStates(StatesGroup):
    waiting_for_start = State()
    waiting_for_end = State()
