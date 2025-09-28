from __future__ import annotations

import logging
from datetime import datetime, timedelta, time
from typing import Awaitable, Callable, Iterable, Optional
from zoneinfo import ZoneInfo

from reminderbot.domain.models import ReminderCreate, ReminderDTO, ReminderUpdate
from reminderbot.infrastructure.db.models import (
    Reminder,
    ReminderLog,
    ReminderRule,
    ReminderStatus,
    RepeatKind,
    ReminderEventStatus,
    User,
)
from reminderbot.infrastructure.repos.reminders import (
    ReminderLogRepository,
    ReminderRepository,
)
from reminderbot.infrastructure.repos.rules import ReminderRuleRepository
from reminderbot.infrastructure.repos.users import UserRepository
from reminderbot.presentation.messages import ReminderRenderer

logger = logging.getLogger(__name__)

SendCallback = Callable[[int, str], Awaitable[None]]


class ReminderService:
    """Бизнес-логика работы с напоминаниями."""

    def __init__(
        self,
        reminders: ReminderRepository,
        rules: ReminderRuleRepository,
        logs: ReminderLogRepository,
        users: UserRepository,
        renderer: ReminderRenderer,
        sender: SendCallback,
    ) -> None:
        self.reminders = reminders
        self.rules = rules
        self.logs = logs
        self.users = users
        self.renderer = renderer
        self.sender = sender
        self.scheduler = None

    def attach_scheduler(self, scheduler) -> None:
        self.scheduler = scheduler

    async def create_reminder(self, user_id: int, payload: ReminderCreate) -> ReminderDTO:
        user = await self._get_user(user_id)
        rule = await self._prepare_rule(payload) if payload.repeat_kind != "none" else None
        reminder = Reminder(
            user_id=user.id,
            rule=rule,
            title=payload.title,
            description=payload.description,
            scheduled_at=self._localize_datetime(payload.scheduled_at, user),
            status=ReminderStatus.ACTIVE,
        )
        await self.reminders.add(reminder)
        await self._schedule_next(reminder)
        return ReminderDTO.model_validate(reminder)

    async def update_reminder(self, reminder_id: int, payload: ReminderUpdate) -> ReminderDTO:
        reminder = await self._require_reminder(reminder_id)
        user = reminder.user
        if payload.title is not None:
            reminder.title = payload.title
        if payload.description is not None:
            reminder.description = payload.description
        if payload.status is not None:
            reminder.status = ReminderStatus(payload.status)
        if payload.scheduled_at is not None:
            reminder.scheduled_at = self._localize_datetime(payload.scheduled_at, user)
        if payload.repeat_kind:
            reminder.rule = await self._upsert_rule(reminder.rule, payload)
        await self._schedule_next(reminder)
        return ReminderDTO.model_validate(reminder)

    async def delete_reminder(self, reminder_id: int) -> None:
        reminder = await self._require_reminder(reminder_id)
        await self.reminders.delete(reminder)
        if self.scheduler:
            self.scheduler.remove_reminder(reminder_id)

    async def get_active_reminders(self) -> Iterable[Reminder]:
        return await self.reminders.list_active()

    async def compute_next_run(self, reminder: Reminder) -> Optional[datetime]:
        if reminder.status != ReminderStatus.ACTIVE:
            return None
        tz = ZoneInfo(reminder.user.timezone)
        now = datetime.now(tz=tz)
        snooze = self._ensure_tz(reminder.snooze_until, tz) if reminder.snooze_until else None
        scheduled = self._ensure_tz(reminder.scheduled_at, tz)
        if snooze and snooze > now:
            return snooze
        if scheduled > now:
            return scheduled
        if reminder.rule is None:
            return None
        return self._next_from_rule(reminder, now)

    async def snooze(self, reminder_id: int, minutes: int) -> ReminderDTO:
        reminder = await self._require_reminder(reminder_id)
        tz = ZoneInfo(reminder.user.timezone)
        now = datetime.now(tz=tz)
        reminder.snooze_until = now + timedelta(minutes=minutes)
        reminder.status = ReminderStatus.SNOOZED
        await self._schedule_next(reminder)
        return ReminderDTO.model_validate(reminder)

    async def close(self, reminder_id: int) -> ReminderDTO:
        reminder = await self._require_reminder(reminder_id)
        reminder.status = ReminderStatus.CLOSED
        reminder.snooze_until = None
        if self.scheduler:
            self.scheduler.remove_reminder(reminder_id)
        return ReminderDTO.model_validate(reminder)

    async def process_and_reschedule(self, reminder_id: int) -> None:
        reminder = await self._require_reminder(reminder_id)
        user = reminder.user
        tz = ZoneInfo(user.timezone)
        now = datetime.now(tz=tz)
        if reminder.status == ReminderStatus.CLOSED:
            logger.info("Напоминание %s закрыто, пропускаем", reminder_id)
            if self.scheduler:
                self.scheduler.remove_reminder(reminder_id)
            return

        if self._is_quiet_time(user, now):
            logger.info("Пользователь %s в тихих часах, переносим", user.id)
            next_time = self._end_of_quiet(now, user)
            reminder.snooze_until = next_time
            reminder.status = ReminderStatus.SNOOZED
            await self._schedule_next(reminder)
            return

        try:
            message = self.renderer.render_reminder(reminder)
            await self.sender(user.telegram_id, message)
            reminder.status = ReminderStatus.ACTIVE
            reminder.snooze_until = None
            await self.logs.add(
                ReminderLog(
                    reminder_id=reminder.id,
                    scheduled_for=self._ensure_tz(reminder.scheduled_at, tz),
                    processed_at=now,
                    status=ReminderEventStatus.SENT,
                )
            )
        except Exception as exc:  # pragma: no cover - критично логируем
            logger.exception("Ошибка отправки напоминания")
            await self.logs.add(
                ReminderLog(
                    reminder_id=reminder.id,
                    scheduled_for=self._ensure_tz(reminder.scheduled_at, tz),
                    processed_at=now,
                    status=ReminderEventStatus.FAILED,
                    error_message=str(exc),
                )
            )
            reminder.snooze_until = now + timedelta(minutes=5)
        finally:
            await self._schedule_next(reminder)

    async def list_user_reminders(self, user_id: int) -> Iterable[ReminderDTO]:
        reminders = await self.reminders.list_for_user(user_id)
        return [ReminderDTO.model_validate(r) for r in reminders]

    async def _schedule_next(self, reminder: Reminder) -> None:
        if not self.scheduler:
            return
        next_run = await self.compute_next_run(reminder)
        if next_run:
            self.scheduler.schedule_reminder(reminder.id, next_run)
        else:
            self.scheduler.remove_reminder(reminder.id)

    async def _prepare_rule(self, payload: ReminderCreate) -> ReminderRule:
        return await self._create_rule(
            RepeatKind(payload.repeat_kind),
            payload.interval,
            payload.custom_interval_minutes,
            payload.weekday_mask,
            payload.monthday,
        )

    async def _upsert_rule(
        self,
        rule: Optional[ReminderRule],
        payload: ReminderUpdate,
    ) -> Optional[ReminderRule]:
        if not payload.repeat_kind or payload.repeat_kind == "none":
            return None
        kind = RepeatKind(payload.repeat_kind)
        interval = payload.interval or (rule.interval if rule else 1)
        rule_data = dict(
            interval=interval,
            custom_interval_minutes=payload.custom_interval_minutes
            if payload.custom_interval_minutes is not None
            else (rule.custom_interval_minutes if rule else None),
            weekday_mask=payload.weekday_mask if payload.weekday_mask is not None else (rule.weekday_mask if rule else None),
            monthday=payload.monthday if payload.monthday is not None else (rule.monthday if rule else None),
        )
        if rule:
            rule.kind = kind
            rule.interval = rule_data["interval"]
            rule.custom_interval_minutes = rule_data["custom_interval_minutes"]
            rule.weekday_mask = rule_data["weekday_mask"]
            rule.monthday = rule_data["monthday"]
            return rule
        return await self._create_rule(
            kind,
            rule_data["interval"],
            rule_data["custom_interval_minutes"],
            rule_data["weekday_mask"],
            rule_data["monthday"],
        )

    async def _create_rule(
        self,
        kind: RepeatKind,
        interval: int,
        custom_minutes: Optional[int],
        weekday_mask: Optional[list[int]],
        monthday: Optional[int],
    ) -> ReminderRule:
        rule = ReminderRule(
            kind=kind,
            interval=interval,
            custom_interval_minutes=custom_minutes,
            weekday_mask=weekday_mask,
            monthday=monthday,
        )
        await self.rules.add(rule)
        return rule

    async def _require_reminder(self, reminder_id: int) -> Reminder:
        reminder = await self.reminders.get_by_id(reminder_id)
        if reminder is None:
            raise ValueError("Напоминание не найдено")
        return reminder

    async def _get_user(self, user_id: int) -> User:
        user = await self.users.get(id=user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        return user

    def _localize_datetime(self, dt: datetime, user: User) -> datetime:
        tz = ZoneInfo(user.timezone)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        return dt.astimezone(tz)

    def _ensure_tz(self, dt: datetime | None, tz: ZoneInfo) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        return dt.astimezone(tz)

    def _next_from_rule(self, reminder: Reminder, reference: datetime) -> Optional[datetime]:
        rule = reminder.rule
        if not rule:
            return None
        base = self._ensure_tz(reminder.scheduled_at, ZoneInfo(reminder.user.timezone))
        if base is None:
            return None
        if rule.kind == RepeatKind.DAILY:
            next_time = base
            while next_time <= reference:
                next_time += timedelta(days=rule.interval)
            return next_time
        if rule.kind == RepeatKind.WEEKLY:
            weekdays = rule.weekday_mask or [base.weekday()]
            return self._next_weekly(reference, base, weekdays, rule.interval)
        if rule.kind == RepeatKind.MONTHLY:
            monthday = rule.monthday or base.day
            return self._next_monthly(reference, base, monthday, rule.interval)
        if rule.kind == RepeatKind.CUSTOM and rule.custom_interval_minutes:
            next_time = base
            delta = timedelta(minutes=rule.custom_interval_minutes)
            while next_time <= reference:
                next_time += delta
            return next_time
        return None

    def _next_weekly(
        self,
        reference: datetime,
        base: datetime,
        weekdays: list[int],
        interval: int,
    ) -> datetime:
        weekdays = sorted(set(weekdays))
        candidate = base
        while candidate <= reference:
            for weekday in weekdays:
                delta_days = (weekday - candidate.weekday()) % 7
                test = candidate + timedelta(days=delta_days)
                test = test.replace(
                    hour=base.hour,
                    minute=base.minute,
                    second=base.second,
                    microsecond=0,
                )
                if test > reference:
                    return test
            candidate += timedelta(days=7 * interval)
        return candidate

    def _next_monthly(
        self,
        reference: datetime,
        base: datetime,
        monthday: int,
        interval: int,
    ) -> datetime:
        year = base.year
        month = base.month
        candidate = base
        while candidate <= reference:
            month += interval
            year += (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(monthday, self._days_in_month(year, month))
            candidate = candidate.replace(year=year, month=month, day=day)
        return candidate

    @staticmethod
    def _days_in_month(year: int, month: int) -> int:
        if month == 2:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            return 28
        if month in {4, 6, 9, 11}:
            return 30
        return 31

    def _is_quiet_time(self, user: User, now: datetime) -> bool:
        start = user.quiet_hours_start
        end = user.quiet_hours_end
        if not start or not end:
            return False
        now_t = time(hour=now.hour, minute=now.minute)
        if start < end:
            return start <= now_t < end
        return now_t >= start or now_t < end

    def _end_of_quiet(self, now: datetime, user: User) -> datetime:
        end = user.quiet_hours_end
        if not end:
            return now
        candidate = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate
