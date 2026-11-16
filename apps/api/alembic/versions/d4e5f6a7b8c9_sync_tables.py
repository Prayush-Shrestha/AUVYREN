"""Sync device registration and change-log tables.

Revision ID: d4e5f6a7b8c9
Revises: c9d0e1f2a3b4
Create Date: 2026-11-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create sync_devices and sync_events tables."""
    op.create_table(
        "sync_devices",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=True),
        sa.Column("app_version", sa.String(length=64), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_sync_devices_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sync_devices"),
    )
    op.create_index(
        "ix_sync_devices_user_id",
        "sync_devices",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "uq_sync_devices_user_device",
        "sync_devices",
        ["user_id", "device_id"],
        unique=True,
    )

    op.create_table(
        "sync_events",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_sync_events_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sync_events"),
    )
    op.create_index(
        "ix_sync_events_user_id",
        "sync_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_sync_events_user_type_created",
        "sync_events",
        ["user_id", "entity_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_sync_events_entity_revision",
        "sync_events",
        ["entity_type", "entity_id", "revision"],
        unique=True,
    )


def downgrade() -> None:
    """Drop sync_events and sync_devices tables."""
    op.drop_index("uq_sync_events_entity_revision", table_name="sync_events")
    op.drop_index("ix_sync_events_user_type_created", table_name="sync_events")
    op.drop_index("ix_sync_events_user_id", table_name="sync_events")
    op.drop_table("sync_events")
    op.drop_index("uq_sync_devices_user_device", table_name="sync_devices")
    op.drop_index("ix_sync_devices_user_id", table_name="sync_devices")
    op.drop_table("sync_devices")
