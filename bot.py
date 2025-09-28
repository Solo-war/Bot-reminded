import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from reminderbot.app.handlers import build_router
from reminderbot.app.middlewares.db import DatabaseSessionMiddleware
from reminderbot.app.middlewares.localization import LocalizationMiddleware
from reminderbot.app.middlewares.services import ServiceMiddleware
from reminderbot.config import get_settings
from reminderbot.infrastructure.db.base import Base
from reminderbot.infrastructure.db.session import create_engine, create_session_factory
from reminderbot.infrastructure.scheduler.service import ReminderScheduler
from reminderbot.infrastructure.scheduler.jobs import init_job_context
from reminderbot.presentation.localization import Localizer
from reminderbot.presentation.messages import ReminderRenderer
from reminderbot.app.utils.commands_setup import setup_bot_commands
from reminderbot.app.middlewares.user_locale import UserLocaleMiddleware


async def main() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.logging_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    localizer = Localizer(settings.locale_dir, settings.default_locale)
    renderer = ReminderRenderer(localizer)
    scheduler = ReminderScheduler(settings, session_factory, bot, renderer)

    # ВАЖНО: инициализируем контекст для джобов до старта планировщика
    init_job_context(session_factory=session_factory, bot=bot, renderer=renderer, scheduler=scheduler)

    await setup_bot_commands(bot, localizer)

    scheduler.start()
    await scheduler.resync()

    # middlewares order: DB -> Services -> i18n -> user-locale
    dp.update.outer_middleware(DatabaseSessionMiddleware(session_factory))
    dp.update.outer_middleware(ServiceMiddleware(settings, renderer, scheduler))
    dp.update.outer_middleware(LocalizationMiddleware(localizer))
    dp.update.outer_middleware(UserLocaleMiddleware())

    router = build_router()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await scheduler.shutdown()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())




