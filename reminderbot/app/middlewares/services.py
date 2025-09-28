from __future__ import annotations

from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from reminderbot.config import Settings
from reminderbot.infrastructure.container import build_reminder_service, build_user_service
from reminderbot.infrastructure.repos.users import UserRepository
from reminderbot.presentation.messages import ReminderRenderer


class ServiceMiddleware(BaseMiddleware):
    """Создаёт сервисы на каждый апдейт."""

    def __init__(
        self,
        settings: Settings,
        renderer: ReminderRenderer,
        scheduler,
    ) -> None:
        self.settings = settings
        self.renderer = renderer
        self.scheduler = scheduler

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data["session"]
        bot = data["bot"]

        user_service = build_user_service(session)
        reminder_service = build_reminder_service(
            session,
            bot,
            self.renderer,
            self.scheduler,
        )

        data.update(
            {
                "settings": self.settings,
                "user_service": user_service,
                "reminder_service": reminder_service,
                "users_repo": UserRepository(session),
                "renderer": self.renderer,
            }
        )

        return await handler(event, data)
