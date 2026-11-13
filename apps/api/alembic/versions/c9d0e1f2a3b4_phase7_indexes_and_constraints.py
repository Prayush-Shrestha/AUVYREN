"""Phase 7 query indexes, note-link integrity, and schema alignment

Revision ID: c9d0e1f2a3b4
Revises: 8b2c3d4e5f6b
Create Date: 2026-11-08 22:30:00.000000

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "8b2c3d4e5f6b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add trigram search indexes and enforce note-link integrity."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        "COMMENT ON COLUMN notes.source_id IS "
        "'Optional link to a goal, project, task, milestone, or routine.'"
    )

    # Duplicate edges can only have come from a retried request; keep the oldest.
    op.execute(
        """
        DELETE FROM note_links a
        USING note_links b
        WHERE a.id > b.id
          AND a.source_note_id = b.source_note_id
          AND a.target_note_id = b.target_note_id
          AND a.link_type = b.link_type
        """
    )
    op.create_unique_constraint(
        "uq_note_links_edge",
        "note_links",
        ["source_note_id", "target_note_id", "link_type"],
    )
    op.create_check_constraint(
        "note_links_no_self_link",
        "note_links",
        "source_note_id <> target_note_id",
    )

    op.create_index(
        "ix_notes_title_trgm",
        "notes",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_notes_content_trgm",
        "notes",
        ["content"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"content": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_notes_tags_trgm",
        "notes",
        ["tags"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"tags": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Remove Phase 7 query indexes and note-link integrity constraints."""
    op.drop_index("ix_notes_tags_trgm", table_name="notes")
    op.drop_index("ix_notes_content_trgm", table_name="notes")
    op.drop_index("ix_notes_title_trgm", table_name="notes")
    op.drop_constraint("note_links_no_self_link", "note_links", type_="check")
    op.drop_constraint("uq_note_links_edge", "note_links", type_="unique")
    op.execute("COMMENT ON COLUMN notes.source_id IS NULL")
