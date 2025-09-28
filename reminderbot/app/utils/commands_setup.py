import asyncio
from aiogram.types import BotCommand

from reminderbot.presentation.commands import get_commands


async def setup_bot_commands(bot, i18n):
    for lang in ("ru", "en", "uk"):
        cmds = get_commands(i18n, lang, is_admin=False)
        await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in cmds], language_code=lang)

