from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from reminderbot.infrastructure.db.models import Reminder
from reminderbot.presentation.localization import Localizer


class ReminderRenderer:
    """Генератор текстов для сообщений пользователю."""

    def __init__(self, localizer: Localizer) -> None:
        self.localizer = localizer

    def render_welcome(self, locale: str | None = None) -> str:
        return self.localizer.translate("common.welcome", locale)

    def render_reminder(self, reminder: Reminder) -> str:
        locale = reminder.user.language
        scheduled = reminder.scheduled_at.astimezone(ZoneInfo(reminder.user.timezone))
        return self.localizer.translate(
            "reminder.notify",
            locale,
            title=reminder.title,
            description=reminder.description or "",
            time=scheduled.strftime("%d.%m.%Y %H:%M"),
        )

    def render_list_item(self, reminder: Reminder) -> str:
        locale = reminder.user.language
        scheduled = reminder.scheduled_at.astimezone(ZoneInfo(reminder.user.timezone))
        status_key = f"reminder.status.{reminder.status.value}"
        return self.localizer.translate(
            "reminder.list_item",
            locale,
            id=reminder.id,
            title=reminder.title,
            status=self.localizer.translate(status_key, locale),
            time=scheduled.strftime("%d.%m.%Y %H:%M"),
        )

    def render_admin_log_entry(self, log) -> str:
        locale = None
        processed_at = log.processed_at or datetime.utcnow()
        return self.localizer.translate(
            "admin.log_entry",
            locale,
            reminder_id=log.reminder_id,
            status=log.status.value,
            time=processed_at.strftime("%d.%m.%Y %H:%M"),
            error=log.error_message or "",
        )
