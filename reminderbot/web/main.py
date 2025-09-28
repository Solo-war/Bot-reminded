from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reminderbot.config import Settings
from reminderbot.infrastructure.repos.reminders import ReminderRepository
from reminderbot.infrastructure.repos.users import UserRepository


def create_app(settings: Settings, session_factory: async_sessionmaker) -> FastAPI:
    app = FastAPI(title="Mercurple Admin", version="0.1.0")

    async def get_session() -> AsyncSession:
        session = session_factory()
        try:
            yield session
            await session.commit()
        finally:
            await session.close()

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "timezone": settings.timezone}

    @app.get("/users")
    async def users(session: AsyncSession = Depends(get_session)) -> list[dict]:
        repo = UserRepository(session)
        users = await repo.list_active()
        return [
            {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "timezone": user.timezone,
                "is_active": user.is_active,
            }
            for user in users
        ]

    @app.get("/reminders/{reminder_id}")
    async def reminder_detail(
        reminder_id: int,
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        repo = ReminderRepository(session)
        reminder = await repo.get_by_id(reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return {
            "id": reminder.id,
            "title": reminder.title,
            "status": reminder.status.value,
            "scheduled_at": reminder.scheduled_at.isoformat(),
            "user_id": reminder.user_id,
        }

    return app
