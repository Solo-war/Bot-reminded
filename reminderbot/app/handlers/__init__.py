from __future__ import annotations

from aiogram import Router

from . import settings, reminders, start


def build_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(settings.router)  # настройки раньше, чтобы не перехватил fallback
    router.include_router(reminders.router)
    return router
