from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from reminderbot.infrastructure.db.models import Reminder, ReminderLog, ReminderStatus

from .base import SQLAlchemyRepository


class ReminderRepository(SQLAlchemyRepository[Reminder]):
    model = Reminder

    async def get_by_id(self, reminder_id: int) -> Optional[Reminder]:
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.user), selectinload(Reminder.rule))
            .where(Reminder.id == reminder_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> Iterable[Reminder]:
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.rule))
            .where(Reminder.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_active(self) -> Iterable[Reminder]:
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.rule), selectinload(Reminder.user))
            .where(Reminder.status == ReminderStatus.ACTIVE)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_due(self, now: datetime) -> Iterable[Reminder]:
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.user), selectinload(Reminder.rule))
            .where(Reminder.status == ReminderStatus.ACTIVE)
            .where(Reminder.scheduled_at <= now)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ReminderLogRepository(SQLAlchemyRepository[ReminderLog]):
    model = ReminderLog

    async def list_for_reminder(self, reminder_id: int) -> Iterable[ReminderLog]:
        stmt = select(ReminderLog).where(ReminderLog.reminder_id == reminder_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
