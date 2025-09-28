from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.ext.asyncio import async_sessionmaker

from reminderbot.config import Settings
from reminderbot.infrastructure.scheduler.jobs import run_reminder_job
from reminderbot.presentation.messages import ReminderRenderer

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Менеджер задач APScheduler для напоминаний."""

    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker,
        bot: Bot,
        renderer: ReminderRenderer,
    ) -> None:
        jobstore = SQLAlchemyJobStore(url=settings.scheduler_url)
        self.scheduler = AsyncIOScheduler(
            jobstores={"default": jobstore}, timezone=settings.timezone
        )
        self.settings = settings
        self.session_factory = session_factory
        self.bot = bot
        self.renderer = renderer

    def start(self) -> None:
        if not self.scheduler.running:
            logger.info("Запуск планировщика напоминаний")
            self.scheduler.start()

    async def shutdown(self) -> None:
        if self.scheduler.running:
            logger.info("Остановка планировщика напоминаний")
            await self.scheduler.shutdown()

    def schedule_reminder(self, reminder_id: int, when: datetime) -> None:
        trigger = DateTrigger(run_date=when.astimezone(ZoneInfo(self.settings.timezone)))
        job_id = self._job_id(reminder_id)
        # Важно: используем модульную функцию run_reminder_job — она сериализуется корректно
        self.scheduler.add_job(
            run_reminder_job,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            args=[reminder_id],
            misfire_grace_time=60,
        )
        logger.debug("Запланировано напоминание %s на %s", reminder_id, when)

    def remove_reminder(self, reminder_id: int) -> None:
        job_id = self._job_id(reminder_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.debug("Удалено напоминание %s из планировщика", reminder_id)

    async def resync(self) -> None:
        from reminderbot.infrastructure.container import build_reminder_service

        logger.info("Синхронизация заданий планировщика")
        async with self.session_factory() as session:
            service = build_reminder_service(session, self.bot, self.renderer, self)
            reminders = await service.get_active_reminders()
            for reminder in reminders:
                next_fire = await service.compute_next_run(reminder)
                if next_fire:
                    self.schedule_reminder(reminder.id, next_fire)

    @staticmethod
    def _job_id(reminder_id: int) -> str:
        return f"reminder:{reminder_id}"
