from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy import select

from reminderbot.infrastructure.db.models import ReminderLog

from .base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class ReminderLogRepository(SQLAlchemyRepository[ReminderLog]):
    model = ReminderLog

    async def list(self, **filters):
        stmt = select(ReminderLog).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()
