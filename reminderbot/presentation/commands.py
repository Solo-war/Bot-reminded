from __future__ import annotations

from typing import List, Tuple

from reminderbot.presentation.localization import Localizer


USER_COMMANDS = [
    ("start", "commands.start"),
    ("help", "commands.help"),
    ("create", "commands.create"),
    ("reminders", "commands.reminders"),
    ("language", "commands.language"),
]


def get_commands(i18n: Localizer, locale: str, is_admin: bool) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for cmd, key in USER_COMMANDS:
        items.append((cmd, i18n.translate(key, locale)))
    return items
