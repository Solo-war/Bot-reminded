from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from reminderbot.config import Settings
from reminderbot.domain.services.reminders import ReminderService
from reminderbot.domain.services.users import UserService
from reminderbot.infrastructure.repos.reminders import ReminderLogRepository, ReminderRepository
from reminderbot.infrastructure.repos.rules import ReminderRuleRepository
from reminderbot.infrastructure.repos.users import UserRepository
from reminderbot.presentation.messages import ReminderRenderer


def build_user_service(session: AsyncSession) -> UserService:
    users_repo = UserRepository(session)
    return UserService(users_repo)


def build_reminder_service(
    session: AsyncSession,
    bot: Bot,
    renderer: ReminderRenderer,
    scheduler,
) -> ReminderService:
    users_repo = UserRepository(session)
    reminders_repo = ReminderRepository(session)
    rules_repo = ReminderRuleRepository(session)
    logs_repo = ReminderLogRepository(session)

    async def sender(chat_id: int, text: str) -> None:
        await bot.send_message(chat_id, text)

    service = ReminderService(
        reminders_repo,
        rules_repo,
        logs_repo,
        users_repo,
        renderer,
        sender,
    )
    service.attach_scheduler(scheduler)
    return service
