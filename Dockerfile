FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml README.md ./
COPY reminderbot ./reminderbot
COPY bot.py ./
COPY alembic ./alembic
COPY tests ./tests

RUN pip install --upgrade pip && \
    pip install .[dev]

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY pyproject.toml README.md ./
COPY reminderbot ./reminderbot
COPY bot.py ./
COPY alembic ./alembic
COPY .env.example ./.env.example

RUN useradd --create-home appuser
USER appuser

CMD ["python", "bot.py"]
