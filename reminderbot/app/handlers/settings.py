from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from reminderbot.domain.services.users import UserService
from reminderbot.presentation.localization import Localizer
from reminderbot.app.keyboards.common import main_menu_kb

router = Router()


def language_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    b = InlineKeyboardBuilder()
    b.button(text="Русский", callback_data="lang:ru")
    b.button(text="English", callback_data="lang:en")
    b.button(text="Українська", callback_data="lang:uk")
    b.adjust(1)
    return b.as_markup()


@router.message(Command("language"))
@router.message(F.text.contains("Языки"))
@router.message(F.text.contains("Мови"))
@router.message(F.text.contains("Languages"))
@router.message(lambda m: m.text and any(x in m.text.lower() for x in ("язык", "мова", "language")))
async def settings_entry(message: Message, i18n: Localizer, locale: str) -> None:
    await message.answer(
        i18n.translate("settings.language_choose", locale),
        reply_markup=language_keyboard(),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def set_language(
    callback: CallbackQuery,
    user_service: UserService,
    i18n: Localizer,
) -> None:
    await callback.answer()
    lang = callback.data.split(":", maxsplit=1)[1]
    profile = await user_service.get_profile(callback.from_user.id)
    if not profile:
        profile = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username,
            language=lang,
        )
    await user_service.update_language(profile.id, lang)
    # Update the language selection message itself to the new locale
    try:
        await callback.message.edit_text(
            i18n.translate("settings.language_choose", lang),
            reply_markup=language_keyboard(),
        )
    except Exception:
        # If editing fails (e.g., message is too old), just send a new one
        await callback.message.answer(
            i18n.translate("settings.language_choose", lang),
            reply_markup=language_keyboard(),
        )

    # Also refresh the main menu keyboard so buttons switch to the new language
    await callback.message.answer(
        i18n.translate("settings.language_updated", lang),
        reply_markup=main_menu_kb(i18n, lang),
    )

