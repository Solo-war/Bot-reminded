from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from reminderbot.infrastructure.db import models  # noqa: F401  # импорт для регистрации


def _prepare_sqlite_path(database_url: str) -> None:
    if database_url.startswith("sqlite"):
        path_part = database_url.split("///")[-1]
        db_path = Path(path_part).expanduser().resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)


def create_engine(database_url: str) -> AsyncEngine:
    _prepare_sqlite_path(database_url)
    return create_async_engine(database_url, future=True, echo=False)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
