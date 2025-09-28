from __future__ import annotations

import enum
from datetime import datetime, time
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ReminderStatus(str, enum.Enum):
    ACTIVE = "active"
    SNOOZED = "snoozed"
    CLOSED = "closed"


class ReminderEventStatus(str, enum.Enum):
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class RepeatKind(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class User(Base):
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    language: Mapped[str] = mapped_column(String(8), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    reminders: Mapped[List["Reminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def quiet_hours(self):
        # Возвращаем маппинг, который Pydantic сможет распарсить в QuietHours
        return {"start": self.quiet_hours_start, "end": self.quiet_hours_end}

class ReminderRule(Base):
    kind: Mapped[RepeatKind] = mapped_column(Enum(RepeatKind), default=RepeatKind.NONE)
    interval: Mapped[int] = mapped_column(Integer, default=1)
    custom_interval_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekday_mask: Mapped[List[int] | None] = mapped_column(JSON, nullable=True)
    monthday: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reminders: Mapped[List["Reminder"]] = relationship(back_populates="rule")


class Reminder(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("reminderrule.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ReminderStatus] = mapped_column(Enum(ReminderStatus), default=ReminderStatus.ACTIVE)
    snooze_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="reminders")
    rule: Mapped[ReminderRule | None] = relationship(back_populates="reminders")
    logs: Mapped[List["ReminderLog"]] = relationship(back_populates="reminder", cascade="all, delete-orphan")


class ReminderLog(Base):
    reminder_id: Mapped[int] = mapped_column(ForeignKey("reminder.id", ondelete="CASCADE"))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ReminderEventStatus] = mapped_column(Enum(ReminderEventStatus))
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    reminder: Mapped[Reminder] = relationship(back_populates="logs")

