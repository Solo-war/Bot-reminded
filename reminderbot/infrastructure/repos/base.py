from __future__ import annotations

from typing import Generic, Iterable, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class SQLAlchemyRepository(Generic[T]):
    """Базовый репозиторий для асинхронной работы с SQLAlchemy."""

    model: type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, **filters) -> Optional[T]:
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, **filters) -> Iterable[T]:
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
