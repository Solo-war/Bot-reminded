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
# Ensure data dir exists and is owned by appuser (copied into named volume on first run)
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

CMD ["python", "bot.py"]
