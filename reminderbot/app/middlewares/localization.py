from __future__ import annotations

from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from reminderbot.presentation.localization import Localizer


class LocalizationMiddleware(BaseMiddleware):
    def __init__(self, localizer: Localizer) -> None:
        self.localizer = localizer

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        locale = getattr(user, "language_code", None)
        data["i18n"] = self.localizer
        data["locale"] = locale or self.localizer.default_locale
        return await handler(event, data)
