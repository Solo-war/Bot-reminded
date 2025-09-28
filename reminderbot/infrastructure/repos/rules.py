from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from reminderbot.infrastructure.db.models import ReminderRule

from .base import SQLAlchemyRepository


class ReminderRuleRepository(SQLAlchemyRepository[ReminderRule]):
    model = ReminderRule

    async def get_by_id(self, rule_id: int) -> Optional[ReminderRule]:
        stmt = select(ReminderRule).where(ReminderRule.id == rule_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, **filters):
        stmt = select(ReminderRule).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()
