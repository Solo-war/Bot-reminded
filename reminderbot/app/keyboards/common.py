from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from reminderbot.presentation.localization import Localizer


def main_menu_kb(i18n: Localizer, locale: str) -> ReplyKeyboardMarkup:
    btn_create = i18n.translate("buttons.main.create", locale)
    btn_list = i18n.translate("buttons.main.list", locale)
    btn_lang = i18n.translate("buttons.main.language", locale)
    btn_help = i18n.translate("buttons.main.help", locale)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_create), KeyboardButton(text=btn_list)],
                  [KeyboardButton(text=btn_lang), KeyboardButton(text=btn_help)]],
        resize_keyboard=True,
    )
    return keyboard


def repeat_keyboard(i18n: Localizer, locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.translate("buttons.repeat.none", locale), callback_data="repeat:none")
    builder.button(text=i18n.translate("buttons.repeat.daily", locale), callback_data="repeat:daily")
    builder.button(text=i18n.translate("buttons.repeat.weekly", locale), callback_data="repeat:weekly")
    builder.button(text=i18n.translate("buttons.repeat.monthly", locale), callback_data="repeat:monthly")
    builder.button(text=i18n.translate("buttons.repeat.custom", locale), callback_data="repeat:custom")
    builder.adjust(1)
    return builder.as_markup()


def reminder_actions_keyboard(i18n: Localizer, locale: str, reminder_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.translate("buttons.actions.edit", locale), callback_data=f"reminder:edit:{reminder_id}")
    builder.button(text=i18n.translate("buttons.actions.snooze", locale), callback_data=f"reminder:snooze:{reminder_id}")
    builder.button(text=i18n.translate("buttons.actions.close", locale), callback_data=f"reminder:close:{reminder_id}")
    builder.button(text=i18n.translate("buttons.actions.delete", locale), callback_data=f"reminder:delete:{reminder_id}")
    builder.adjust(2)
    return builder.as_markup()
