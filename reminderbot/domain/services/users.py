from __future__ import annotations

from datetime import time
from typing import Optional

from reminderbot.domain.models import QuietHours, UserProfile
from reminderbot.infrastructure.db.models import User
from reminderbot.infrastructure.repos.users import UserRepository


class UserService:
    """Бизнес-логика, связанная с пользователями."""

    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def get_or_create_user(
        self,
        telegram_id: int,
        full_name: Optional[str],
        username: Optional[str],
        language: Optional[str],
    ) -> UserProfile:
        user = await self.users.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                language=language or "ru",
            )
            await self.users.add(user)
        else:
            user.full_name = full_name or user.full_name
            user.username = username or user.username
            if language:
                user.language = language
        return UserProfile.model_validate(user)

    async def update_language(self, user_id: int, language: str) -> None:
        user = await self.users.get(id=user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.language = language

    async def update_timezone(self, user_id: int, timezone: str) -> None:
        user = await self.users.get(id=user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.timezone = timezone

    async def update_quiet_hours(
        self,
        user_id: int,
        quiet_start: Optional[time],
        quiet_end: Optional[time],
    ) -> QuietHours:
        user = await self.users.get(id=user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.quiet_hours_start = quiet_start
        user.quiet_hours_end = quiet_end
        return QuietHours(start=quiet_start, end=quiet_end)

    async def set_active(self, user_id: int, active: bool) -> None:
        user = await self.users.get(id=user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.is_active = active

    async def get_profile(self, telegram_id: int) -> Optional[UserProfile]:
        user = await self.users.get_by_telegram_id(telegram_id)
        if user:
            return UserProfile.model_validate(user)
        return None
