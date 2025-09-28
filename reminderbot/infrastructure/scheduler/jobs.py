from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import async_sessionmaker
from aiogram import Bot

from reminderbot.presentation.messages import ReminderRenderer
from reminderbot.infrastructure.container import build_reminder_service

logger = logging.getLogger(__name__)

# Глобальный контекст для джобов планировщика (инициализируется при старте)
JOB_CTX: dict[str, object] = {}


def init_job_context(*, session_factory: async_sessionmaker, bot: Bot, renderer: ReminderRenderer, scheduler) -> None:
    JOB_CTX["session_factory"] = session_factory
    JOB_CTX["bot"] = bot
    JOB_CTX["renderer"] = renderer
    JOB_CTX["scheduler"] = scheduler


async def run_reminder_job(reminder_id: int) -> None:
    """Функция уровня модуля для APScheduler (легко сериализуется)."""
    session_factory: async_sessionmaker = JOB_CTX["session_factory"]  # type: ignore[assignment]
    bot: Bot = JOB_CTX["bot"]  # type: ignore[assignment]
    renderer: ReminderRenderer = JOB_CTX["renderer"]  # type: ignore[assignment]
    scheduler = JOB_CTX.get("scheduler")

    async with session_factory() as session:
        service = build_reminder_service(session, bot, renderer, scheduler)
        await service.process_and_reschedule(reminder_id)
        await session.commit()
