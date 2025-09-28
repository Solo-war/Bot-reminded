from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol


class CalendarIntegration(ABC):
    """Интерфейс для внешних календарей."""

    @abstractmethod
    async def export_reminder(
        self,
        title: str,
        start: datetime,
        end: datetime | None,
        description: str | None,
        timezone: str,
    ) -> str:
        """Создаёт событие и возвращает внешний идентификатор."""


class NullCalendarIntegration(CalendarIntegration):
    async def export_reminder(
        self,
        title: str,
        start: datetime,
        end: datetime | None,
        description: str | None,
        timezone: str,
    ) -> str:
        return ""
