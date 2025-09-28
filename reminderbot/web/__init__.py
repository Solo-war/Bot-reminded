from __future__ import annotations

from reminderbot.config import get_settings
from reminderbot.infrastructure.db.session import create_engine, create_session_factory
from reminderbot.web.main import create_app


def build_app():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    return create_app(settings, session_factory)


app = build_app()
