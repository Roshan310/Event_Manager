"""Accounts, discovery, attendance, and durable background work.

Revision ID: 0002_complete_events
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0002_complete_events"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, columns in {
        "users": ("created_at", "updated_at"),
        "events": ("created_at", "updated_at"),
        "registrations": ("created_at", "updated_at"),
        "refresh_tokens": ("created_at",),
        "outbox_messages": ("created_at",),
    }.items():
        for column in columns:
            op.execute(sa.text(f"UPDATE {table} SET {column}=now() WHERE {column} IS NULL"))
            op.alter_column(table, column, nullable=False)
    op.create_index("ix_events_title", "events", ["title"])
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "users",
        sa.Column("reminder_emails", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "categories",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.add_column(
        "events",
        sa.Column(
            "category_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
        ),
    )
    op.create_index("ix_events_category_id", "events", ["category_id"])
    op.add_column("events", sa.Column("cover_filename", sa.String(80)))
    op.add_column("events", sa.Column("revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "events",
        sa.Column("ever_published", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE events SET ever_published = true WHERE status != 'draft'")
    op.add_column("registrations", sa.Column("queued_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE registrations SET queued_at = created_at")
    op.alter_column("registrations", "queued_at", nullable=False, server_default=sa.func.now())
    op.add_column("registrations", sa.Column("ticket_nonce", sa.String()))
    op.add_column("registrations", sa.Column("checked_in_at", sa.DateTime(timezone=True)))
    op.add_column("registrations", sa.Column("checked_in_by", pg.UUID(as_uuid=True)))
    op.create_index(
        "ix_registration_queue", "registrations", ["event_id", "status", "queued_at", "id"]
    )
    op.add_column("outbox_messages", sa.Column("claim_id", pg.UUID(as_uuid=True)))
    op.add_column("outbox_messages", sa.Column("lease_until", sa.DateTime(timezone=True)))
    op.add_column("outbox_messages", sa.Column("dedupe_key", sa.String(200)))
    op.create_unique_constraint("uq_outbox_dedupe", "outbox_messages", ["dedupe_key"])
    op.create_index(
        "ix_outbox_due",
        "outbox_messages",
        ["available_at", "created_at"],
        postgresql_where=sa.text("processed_at IS NULL AND failed_at IS NULL"),
    )
    op.create_table(
        "bookmarks",
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "event_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "action_tokens",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_action_tokens_user_id", "action_tokens", ["user_id"])
    op.create_index("ix_action_tokens_expires_at", "action_tokens", ["expires_at"])
    op.create_table(
        "notifications",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id", pg.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE")
        ),
        sa.Column("topic", sa.String(80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("dedupe_key", sa.String(200), unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("read_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", pg.UUID(as_uuid=True)),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("target_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"])
    op.create_table(
        "rate_buckets",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rate_buckets_expires_at", "rate_buckets", ["expires_at"])
    op.create_table(
        "worker_heartbeat",
        sa.Column("name", sa.String(80), primary_key=True),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Existing JWTs have no session claim and are deliberately invalidated on upgrade.
    op.execute("UPDATE refresh_tokens SET revoked_at = now() WHERE revoked_at IS NULL")


def downgrade() -> None:
    op.drop_index("ix_events_title", table_name="events")
    for table, columns in {
        "users": ("created_at", "updated_at"),
        "events": ("created_at", "updated_at"),
        "registrations": ("created_at", "updated_at"),
        "refresh_tokens": ("created_at",),
        "outbox_messages": ("created_at",),
    }.items():
        for column in columns:
            op.alter_column(table, column, nullable=True)
    for table in (
        "worker_heartbeat",
        "rate_buckets",
        "audit_logs",
        "notifications",
        "action_tokens",
        "bookmarks",
    ):
        op.drop_table(table)
    op.drop_index("ix_outbox_due", table_name="outbox_messages")
    for column in ("dedupe_key", "lease_until", "claim_id"):
        op.drop_column("outbox_messages", column)
    op.drop_index("ix_registration_queue", table_name="registrations")
    for column in ("checked_in_by", "checked_in_at", "ticket_nonce", "queued_at"):
        op.drop_column("registrations", column)
    for column in ("ever_published", "revision", "cover_filename", "category_id"):
        op.drop_column("events", column)
    op.drop_table("categories")
    for column in ("reminder_emails", "auth_version", "email_verified"):
        op.drop_column("users", column)
