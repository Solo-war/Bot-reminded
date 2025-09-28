from __future__ import annotations

from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DatabaseSessionMiddleware(BaseMiddleware):
    """Создаёт сессию БД на время обработки апдейта."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session = self.session_factory()
        data["session"] = session
        try:
            result = await handler(event, data)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
