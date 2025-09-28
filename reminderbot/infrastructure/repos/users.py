from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select

from reminderbot.infrastructure.db.models import User

from .base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> Iterable[User]:
        stmt = select(User).where(User.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()
