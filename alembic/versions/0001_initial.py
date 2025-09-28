from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="ru"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.UniqueConstraint("telegram_id", name="uq_user_telegram_id"),
    )

    op.create_index("ix_user_telegram_id", "user", ["telegram_id"], unique=False)

    op.create_table(
        "reminderrule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("kind", sa.Enum("none", "daily", "weekly", "monthly", "custom", name="repeatkind"), nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("custom_interval_minutes", sa.Integer(), nullable=True),
        sa.Column("weekday_mask", sa.JSON(), nullable=True),
        sa.Column("monthday", sa.Integer(), nullable=True),
    )

    op.create_table(
        "reminder",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("reminderrule.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Enum("active", "snoozed", "closed", name="reminderstatus"), nullable=False, server_default="active"),
        sa.Column("snooze_until", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "reminderlog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("reminder_id", sa.Integer(), sa.ForeignKey("reminder.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("sent", "skipped", "failed", name="remindereventstatus"), nullable=False),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("reminderlog")
    op.drop_table("reminder")
    op.drop_table("reminderrule")
    op.drop_index("ix_user_telegram_id", table_name="user")
    op.drop_table("user")
