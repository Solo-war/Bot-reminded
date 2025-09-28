# Mercurple Reminderbot

Mercurple — Telegram-бот, который помогает создавать, управлять и доставлять напоминания с поддержкой повторов, тихих часов и админ-функций. Проект построен на Python 3.11, aiogram 3 и APScheduler.

## Архитектура
- `bot.py` — точка входа, инициализация логирования, БД, планировщика и запуск polling.
- `reminderbot/app` — работа с Telegram API: роутеры, FSM-диалоги, клавиатуры, middleware.
- `reminderbot/domain` — бизнес-логика и DTO, сервисы пользователей и напоминаний.
- `reminderbot/infrastructure` — SQLAlchemy ORM, репозитории, контейнеры зависимостей, планировщик, интеграции.
- `reminderbot/presentation` — локализация и шаблоны сообщений.
- `reminderbot/web` — опциональная FastAPI-панель для мониторинга.
- `alembic` — настройка миграций.
- `tests` — pytest-покрытие ключевых сценариев домена.

## Запуск локально
1. Скопируйте `.env.example` в `.env` и заполните `BOT_TOKEN` и другие переменные.
2. Установите зависимости:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows
   pip install -e .[dev]
   ```
3. Примените миграции (опционально):
   ```bash
   alembic upgrade head
   ```
4. Запустите бота:
   ```bash
   python bot.py
   ```

## Docker
- Сборка и запуск:
  ```bash
  docker compose up --build
  ```
- Сервис `bot` запускает Telegram-бота, `web` — FastAPI-панель на `http://localhost:8000`.

## Тестирование
- Запуск pytest:
  ```bash
  pytest
  ```
- Тесты покрывают расчёт повторов и логику тихих часов.

## Планировщик и уведомления
- APScheduler сохраняет задания в SQLite (`data/scheduler.db`).
- Напоминания пересчитываются при CRUD-операциях и перезапуске за счёт `ReminderScheduler.resync()`.
- Тихие часы определяются на уровне пользователя и учитываются при отправке.

