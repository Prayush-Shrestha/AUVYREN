"""Request and response schemas for knowledge workspace (notes, links)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.knowledge import NoteKind, NoteSourceType


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoteCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=240)
    content: str | None = Field(default=None, max_length=50000)
    kind: NoteKind = NoteKind.NOTE
    source_type: NoteSourceType = NoteSourceType.USER
    source_id: uuid.UUID | None = None
    tags: str | None = Field(default=None, max_length=255)


class NoteUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    content: str | None = Field(default=None, max_length=50000)
    kind: NoteKind | None = None
    source_type: NoteSourceType | None = None
    source_id: uuid.UUID | None = None
    tags: str | None = Field(default=None, max_length=255)


class NoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str | None
    kind: NoteKind
    source_type: NoteSourceType
    source_id: uuid.UUID | None
    tags: str | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]


class NoteLinkCreate(_StrictModel):
    source_note_id: uuid.UUID
    target_note_id: uuid.UUID
    link_type: str = Field(min_length=1, max_length=32, default="relates_to")


class NoteLinkResponse(BaseModel):
    id: uuid.UUID
    source_note_id: uuid.UUID
    target_note_id: uuid.UUID
    link_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchRequest(_StrictModel):
    q: str = Field(min_length=1, max_length=240)
    kind: NoteKind | None = None
    limit: int = Field(default=50, ge=1, le=200)


class KnowledgeSearchResponse(BaseModel):
    notes: list[NoteResponse]
    total: int
