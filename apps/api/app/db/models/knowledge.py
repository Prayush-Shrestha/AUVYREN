"""Knowledge workspace models: notes, knowledge entries, and note links."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import enum_type

if TYPE_CHECKING:
    from app.db.models.user import User


class NoteKind(StrEnum):
    NOTE = "note"
    JOURNAL = "journal"
    DECISION = "decision"
    REVIEW = "review"


class NoteSourceType(StrEnum):
    USER = "user"
    GENERATED = "generated"


class Note(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A user-authored or AI-generated note, journal entry, decision record,
    or review within the knowledge workspace."""

    __tablename__ = "notes"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('note', 'journal', 'decision', 'review')",
            name="notes_kind_check",
        ),
        Index("ix_notes_user_kind", "user_id", "kind"),
        Index("ix_notes_user_created", "user_id", "created_at"),
        Index("ix_notes_source", "source_type", "source_id"),
        Index(
            "ix_notes_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        Index(
            "ix_notes_content_trgm",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
        ),
        Index(
            "ix_notes_tags_trgm",
            "tags",
            postgresql_using="gin",
            postgresql_ops={"tags": "gin_trgm_ops"},
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[NoteKind] = mapped_column(
        enum_type(NoteKind, "note_kind"),
        nullable=False,
        default=NoteKind.NOTE,
        server_default=NoteKind.NOTE.value,
    )
    source_type: Mapped[NoteSourceType] = mapped_column(
        enum_type(NoteSourceType, "note_source_type"),
        nullable=False,
        default=NoteSourceType.USER,
        server_default=NoteSourceType.USER.value,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36), nullable=True,
        comment="Optional link to a goal, project, task, milestone, or routine.",
    )
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", back_populates="notes")
    source_links: Mapped[list[NoteLink]] = relationship(
        "NoteLink",
        back_populates="source_note",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="NoteLink.source_note_id",
    )
    target_links: Mapped[list[NoteLink]] = relationship(
        "NoteLink",
        back_populates="target_note",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="NoteLink.target_note_id",
    )


class NoteLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A typed link between two notes, representing a knowledge graph edge."""

    __tablename__ = "note_links"
    __table_args__ = (
        UniqueConstraint(
            "source_note_id",
            "target_note_id",
            "link_type",
            name="uq_note_links_edge",
        ),
        CheckConstraint(
            "source_note_id <> target_note_id",
            name="note_links_no_self_link",
        ),
        Index("ix_note_links_source", "source_note_id"),
        Index("ix_note_links_target", "target_note_id"),
        Index("ix_note_links_type", "link_type"),
    )

    source_note_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    target_note_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(String(32), nullable=False)

    source_note: Mapped[Note] = relationship(
        "Note", back_populates="source_links", foreign_keys=[source_note_id]
    )
    target_note: Mapped[Note] = relationship(
        "Note", back_populates="target_links", foreign_keys=[target_note_id]
    )
