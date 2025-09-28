from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from reminderbot.app.keyboards.common import (
    main_menu_kb,
    reminder_actions_keyboard,
    repeat_keyboard,
)
from reminderbot.app.utils.states import CreateReminderStates, SnoozeReminderStates
from reminderbot.app.utils.calendar import calendar_keyboard, hours_keyboard, minutes_keyboard
from reminderbot.domain.models import ReminderCreate
from reminderbot.domain.services.reminders import ReminderService
from reminderbot.domain.services.users import UserService
from reminderbot.presentation.localization import Localizer
from reminderbot.presentation.messages import ReminderRenderer


router = Router()


@router.message(Command("create"))
@router.message(F.text.contains("Создать"))
@router.message(F.text.contains("Створити"))
@router.message(F.text.contains("Create"))
async def start_create(message: Message, state: FSMContext, i18n: Localizer, locale: str) -> None:
    await state.set_state(CreateReminderStates.waiting_for_title)
    await message.answer(
        i18n.translate("create.title_prompt", locale),
        reply_markup=main_menu_kb(i18n, locale),
    )


@router.message(StateFilter(CreateReminderStates.waiting_for_title))
async def capture_title(message: Message, state: FSMContext, i18n: Localizer, locale: str) -> None:
    await state.update_data(title=(message.text or "").strip())
    today = datetime.now().date()
    await state.set_state(CreateReminderStates.waiting_for_date)
    await message.answer(
        i18n.translate("create.date_prompt", locale),
        reply_markup=calendar_keyboard(i18n, locale, today.year, today.month),
    )


@router.callback_query(StateFilter(CreateReminderStates.waiting_for_date), F.data.startswith("cal:"))
async def on_calendar(callback: CallbackQuery, state: FSMContext, i18n: Localizer, locale: str) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    action = parts[1]
    if action == "noop":
        return
    if action == "nav":
        ym = parts[2]
        year, month = map(int, ym.split("-"))
        await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(i18n, locale, year, month))
        return
    if action == "pick":
        ymd = parts[2]
        await state.update_data(date=ymd)
        await state.set_state(CreateReminderStates.waiting_for_time_hour)
        await callback.message.answer(i18n.translate("create.hour_prompt", locale), reply_markup=hours_keyboard())
        return


@router.callback_query(StateFilter(CreateReminderStates.waiting_for_time_hour), F.data.startswith("time:hour:"))
async def on_hour(callback: CallbackQuery, state: FSMContext, i18n: Localizer, locale: str) -> None:
    await callback.answer()
    hour = int(callback.data.split(":")[2])
    await state.update_data(hour=hour)
    await state.set_state(CreateReminderStates.waiting_for_time_minute)
    await callback.message.answer(i18n.translate("create.minute_prompt", locale), reply_markup=minutes_keyboard(hour))


@router.callback_query(StateFilter(CreateReminderStates.waiting_for_time_minute))
async def on_minute(
    callback: CallbackQuery,
    state: FSMContext,
    reminder_service: ReminderService,
    user_service: UserService,
    i18n: Localizer,
    locale: str,
) -> None:
    if not callback.data.startswith("time:"):
        await callback.answer()
        return
    await callback.answer()
    parts = callback.data.split(":")
    if parts[1] == "back_hours":
        await state.set_state(CreateReminderStates.waiting_for_time_hour)
        await callback.message.answer(i18n.translate("create.hour_prompt", locale), reply_markup=hours_keyboard())
        return
    if parts[1] != "min":
        return
    _, _, hour_str, minute_str = parts
    data = await state.get_data()
    profile = await user_service.get_profile(callback.from_user.id)
    user_id = profile.id if profile else None
    if not user_id:
        profile = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username,
            language=callback.from_user.language_code,
        )
        user_id = profile.id
    y, m, d = map(int, data["date"].split("-"))
    h, mi = int(hour_str), int(minute_str)
    scheduled_dt = datetime(year=y, month=m, day=d, hour=h, minute=mi)
    await state.update_data(scheduled_at=scheduled_dt.isoformat())
    await state.set_state(CreateReminderStates.waiting_for_repeat)
    await callback.message.answer(
        i18n.translate("create.repeat_prompt", locale),
        reply_markup=repeat_keyboard(i18n, locale),
    )


@router.callback_query(StateFilter(CreateReminderStates.waiting_for_repeat), F.data.startswith("repeat:"))
async def choose_repeat(
    callback: CallbackQuery,
    state: FSMContext,
    reminder_service: ReminderService,
    user_service: UserService,
    i18n: Localizer,
    locale: str,
) -> None:
    await callback.answer()
    repeat = callback.data.split(":", maxsplit=1)[1]
    data = await state.get_data()
    profile = await user_service.get_profile(callback.from_user.id)
    user_id = profile.id if profile else None
    if not user_id:
        profile = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username,
            language=callback.from_user.language_code,
        )
        user_id = profile.id
    scheduled = datetime.fromisoformat(data["scheduled_at"])
    payload = ReminderCreate(
        title=data["title"],
        description=None,
        scheduled_at=scheduled,
        repeat_kind=repeat,
    )
    reminder = await reminder_service.create_reminder(user_id, payload)
    text = i18n.translate(
        "reminder.created",
        locale,
        title=reminder.title,
        time=reminder.scheduled_at.strftime("%d.%m.%Y %H:%M"),
    )
    await callback.message.answer(text, reply_markup=main_menu_kb(i18n, locale))
    await state.clear()


@router.message(Command("reminders"))
@router.message(F.text.contains("Список"))
@router.message(F.text.contains("List"))
async def list_reminders(
    message: Message,
    reminder_service: ReminderService,
    user_service: UserService,
    renderer: ReminderRenderer,
    i18n: Localizer,
    locale: str,
) -> None:
    profile = await user_service.get_profile(message.from_user.id)
    if not profile:
        await message.answer(i18n.translate("reminder.list_empty", locale))
        return
    reminders = await reminder_service.list_user_reminders(profile.id)
    if not reminders:
        await message.answer(i18n.translate("reminder.list_empty", locale))
        return
    lines = [i18n.translate("reminder.list_title", locale)]
    for dto in reminders:
        reminder = await reminder_service.reminders.get_by_id(dto.id)  # type: ignore[attr-defined]
        if reminder:
            await message.answer(
                renderer.render_list_item(reminder),
                reply_markup=reminder_actions_keyboard(i18n, locale, reminder.id),
            )
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("reminder:snooze:"))
async def snooze_prompt(callback: CallbackQuery, state: FSMContext, i18n: Localizer, locale: str) -> None:
    reminder_id = int(callback.data.split(":")[-1])
    await state.update_data(reminder_id=reminder_id)
    await state.set_state(SnoozeReminderStates.waiting_for_minutes)
    await callback.message.answer(i18n.translate("snooze.prompt", locale))
    await callback.answer()


@router.message(StateFilter(SnoozeReminderStates.waiting_for_minutes))
async def apply_snooze(
    message: Message,
    state: FSMContext,
    reminder_service: ReminderService,
    i18n: Localizer,
    locale: str,
) -> None:
    data = await state.get_data()
    await state.clear()
    try:
        minutes = int((message.text or "").strip())
    except ValueError:
        await message.answer(i18n.translate("snooze.invalid_number", locale))
        return
    await reminder_service.snooze(data["reminder_id"], minutes)
    await message.answer(
        i18n.translate("reminder.snoozed", locale, minutes=minutes),
        reply_markup=main_menu_kb(i18n, locale),
    )


@router.callback_query(F.data.startswith("reminder:delete:"))
async def delete_reminder(
    callback: CallbackQuery,
    reminder_service: ReminderService,
    i18n: Localizer,
    locale: str,
) -> None:
    reminder_id = int(callback.data.split(":")[-1])
    await reminder_service.delete_reminder(reminder_id)
    await callback.message.edit_reply_markup()
    await callback.message.answer(i18n.translate("reminder.deleted", locale))
    await callback.answer()


@router.callback_query(F.data.startswith("reminder:close:"))
async def close_reminder(
    callback: CallbackQuery,
    reminder_service: ReminderService,
    i18n: Localizer,
    locale: str,
) -> None:
    reminder_id = int(callback.data.split(":")[-1])
    await reminder_service.close(reminder_id)
    await callback.message.answer(i18n.translate("reminder.closed", locale))
    await callback.answer()


@router.callback_query(F.data.startswith("reminder:edit:"))
async def edit_not_implemented(callback: CallbackQuery, i18n: Localizer, locale: str) -> None:
    await callback.answer(i18n.translate("edit.not_implemented", locale))


@router.message()
async def fallback_handler(message: Message, i18n: Localizer, locale: str) -> None:
    try:
        await message.reply(i18n.translate("common.use_commands", locale))
    except TelegramBadRequest:
        pass

