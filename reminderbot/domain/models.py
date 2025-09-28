from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class QuietHours(BaseModel):
    start: Optional[time]
    end: Optional[time]


class ReminderRuleDTO(BaseModel):
    id: int
    kind: str
    interval: int
    custom_interval_minutes: Optional[int]
    weekday_mask: Optional[List[int]]
    monthday: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class ReminderDTO(BaseModel):
    id: int
    title: str
    description: Optional[str]
    scheduled_at: datetime
    status: str
    snooze_until: Optional[datetime]
    rule: Optional[ReminderRuleDTO]

    model_config = ConfigDict(from_attributes=True)


class ReminderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    repeat_kind: str = "none"
    interval: int = 1
    custom_interval_minutes: Optional[int] = None
    weekday_mask: Optional[List[int]] = None
    monthday: Optional[int] = None


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    repeat_kind: Optional[str] = None
    interval: Optional[int] = None
    custom_interval_minutes: Optional[int] = None
    weekday_mask: Optional[List[int]] = None
    monthday: Optional[int] = None
    status: Optional[str] = None


class UserProfile(BaseModel):
    id: int
    telegram_id: int
    full_name: Optional[str]
    username: Optional[str]
    timezone: str
    language: str
    is_active: bool
    quiet_hours: QuietHours

    model_config = ConfigDict(from_attributes=True)
