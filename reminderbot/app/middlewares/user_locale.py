from __future__ import annotations

from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class UserLocaleMiddleware(BaseMiddleware):
    """Выставляет locale из профиля пользователя (приоритетнее чем язык Telegram)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_service = data.get("user_service")
        from_user = data.get("event_from_user")
        if user_service and from_user:
            try:
                profile = await user_service.get_profile(from_user.id)
                if profile and getattr(profile, "language", None):
                    data["locale"] = profile.language
            except Exception:
                pass
        return await handler(event, data)
