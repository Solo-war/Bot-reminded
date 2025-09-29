from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 

class Settings(BaseSettings):
    """Настройки приложения, читаются из .env при наличии."""

    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/reminderbot.db", alias="DATABASE_URL"
    )
    scheduler_database_url: str | None = Field(
        default=None, alias="SCHEDULER_DATABASE_URL"
    )
    timezone: str = Field(default="UTC", alias="DEFAULT_TIMEZONE")
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    locale_dir: Path = Field(
        default=Path("reminderbot/presentation/locales"), alias="LOCALE_DIR"
    )
    default_locale: str = Field(default="ru", alias="DEFAULT_LOCALE")
    quiet_hours_start: int = Field(default=22, alias="QUIET_HOURS_START")
    quiet_hours_end: int = Field(default=7, alias="QUIET_HOURS_END")
    web_enabled: bool = Field(default=True, alias="WEB_ENABLED")
    web_host: str = Field(default="0.0.0.0", alias="WEB_HOST")
    web_port: int = Field(default=8000, alias="WEB_PORT")
    google_credentials_path: Path | None = Field(
        default=None, alias="GOOGLE_CREDENTIALS_PATH"
    )
    logging_level: str = Field(default="INFO", alias="LOGGING_LEVEL")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        str_strip_whitespace=True,
    )

    @model_validator(mode="after")
    def _split_admin_ids(self) -> "Settings":
        if self.admin_ids and isinstance(self.admin_ids, list):
            return self
        if isinstance(self.admin_ids, str):
            values = [item.strip() for item in self.admin_ids.split(",") if item.strip()]
            object.__setattr__(self, "admin_ids", [int(v) for v in values])
        return self

    @property
    def scheduler_url(self) -> str:
        """Возвращает URL хранилища задач APScheduler."""

        if self.scheduler_database_url:
            return self.scheduler_database_url
        return "sqlite:///./data/scheduler.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

