from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from reminderbot.app.keyboards.common import main_menu_kb
from reminderbot.domain.services.users import UserService
from reminderbot.presentation.commands import get_commands
from reminderbot.presentation.localization import Localizer
from reminderbot.presentation.messages import ReminderRenderer
from reminderbot.config import Settings

router = Router()


@router.message(CommandStart())
async def handle_start(
    message: Message,
    user_service: UserService,
    renderer: ReminderRenderer,
    i18n: Localizer,
) -> None:
    profile = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        language=message.from_user.language_code,
    )
    text = renderer.render_welcome(profile.language)
    await message.answer(text, reply_markup=main_menu_kb(i18n, profile.language))


@router.message(Command("help"))
@router.message(F.text == "🛑 Помощь")
@router.message(lambda m: m.text and ("help" in m.text.lower() or "помощ" in m.text.lower() or "довід" in m.text.lower()))
async def handle_help(
    message: Message,
    settings: Settings,
    i18n: Localizer,
    locale: str,
) -> None:
    is_admin = message.from_user.id in settings.admin_ids
    cmds = get_commands(i18n, locale, is_admin)
    lines = [i18n.translate("help.title", locale)]
    for cmd, desc in cmds:
        lines.append(f"/{cmd} - {desc}")
    await message.answer("\n".join(lines), reply_markup=main_menu_kb(i18n, locale))


@router.message(F.text.contains("Помощь"))
@router.message(F.text.contains("Help"))
@router.message(F.text.contains("Допомога"))
async def handle_help_btn(
    message: Message,
    settings: Settings,
    i18n: Localizer,
    locale: str,
) -> None:
    await handle_help(message, settings, i18n, locale)
