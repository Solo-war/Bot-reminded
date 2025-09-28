import asyncio
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from reminderbot.domain.models import ReminderCreate
from reminderbot.infrastructure.db.base import Base
from reminderbot.infrastructure.db.models import ReminderStatus, RepeatKind, User
from reminderbot.infrastructure.repos.reminders import ReminderLogRepository, ReminderRepository
from reminderbot.infrastructure.repos.rules import ReminderRuleRepository
from reminderbot.infrastructure.repos.users import UserRepository
from reminderbot.presentation.localization import Localizer
from reminderbot.presentation.messages import ReminderRenderer
from reminderbot.domain.services.reminders import ReminderService


class DummyScheduler:
    def __init__(self):
        self.jobs = {}

    def schedule_reminder(self, reminder_id: int, when: datetime) -> None:
        self.jobs[reminder_id] = when

    def remove_reminder(self, reminder_id: int) -> None:
        self.jobs.pop(reminder_id, None)


@pytest.fixture(scope="module")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def renderer() -> ReminderRenderer:
    localizer = Localizer(Path("reminderbot/presentation/locales"), "ru")
    return ReminderRenderer(localizer)


@pytest.fixture
def scheduler() -> DummyScheduler:
    return DummyScheduler()


@pytest.fixture
async def reminder_service(session: AsyncSession, renderer: ReminderRenderer, scheduler: DummyScheduler) -> ReminderService:
    users_repo = UserRepository(session)
    reminders_repo = ReminderRepository(session)
    rules_repo = ReminderRuleRepository(session)
    logs_repo = ReminderLogRepository(session)

    async def sender(chat_id: int, text: str) -> None:
        return None

    service = ReminderService(reminders_repo, rules_repo, logs_repo, users_repo, renderer, sender)
    service.attach_scheduler(scheduler)

    user = User(
        telegram_id=1,
        timezone="UTC",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
    )
    await users_repo.add(user)
    await session.flush()
    return service


@pytest.mark.asyncio
async def test_compute_next_run_daily(reminder_service: ReminderService, scheduler: DummyScheduler):
    user = await reminder_service.users.get_by_telegram_id(1)
    assert user is not None
    base_time = datetime.now(tz=ZoneInfo("UTC")) - timedelta(days=1)
    payload = ReminderCreate(
        title="Тест",
        scheduled_at=base_time,
        repeat_kind=RepeatKind.DAILY.value,
    )
    reminder = await reminder_service.create_reminder(user.id, payload)
    scheduled = scheduler.jobs[reminder.id]
    assert scheduled > datetime.now(tz=ZoneInfo("UTC"))
    assert reminder.status == ReminderStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_quiet_hours_delays(reminder_service: ReminderService, scheduler: DummyScheduler):
    user = await reminder_service.users.get_by_telegram_id(1)
    assert user is not None
    user.quiet_hours_start = time(22, 0)
    user.quiet_hours_end = time(7, 0)
    reminder = await reminder_service.reminders.get_by_id(1)
    assert reminder is not None
    reminder.scheduled_at = datetime.now(tz=ZoneInfo("UTC"))
    await reminder_service.process_and_reschedule(reminder.id)
    assert reminder.snooze_until is not None
    assert reminder.snooze_until.hour == 7
