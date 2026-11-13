"""Knowledge workspace service: notes, links, and search."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import Note, NoteKind, NoteLink, NoteSourceType
from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    NoteCreate,
    NoteUpdate,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


async def get_note_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, note_id: uuid.UUID
) -> Note | None:
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user_id,
            Note.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_note(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: NoteCreate,
) -> Note:
    note = Note(
        user_id=user_id,
        title=payload.title,
        content=payload.content,
        kind=payload.kind,
        source_type=payload.source_type,
        source_id=str(payload.source_id) if payload.source_id else None,
        tags=payload.tags,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return note


async def update_note(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
    payload: NoteUpdate,
) -> Note | None:
    note = await get_note_by_id(db, user_id=user_id, note_id=note_id)
    if note is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    if data.get("source_id") is not None:
        data["source_id"] = str(data["source_id"])
    for field, value in data.items():
        setattr(note, field, value)

    await db.flush()
    await db.refresh(note)
    return note


async def delete_note(
    db: AsyncSession, *, user_id: uuid.UUID, note_id: uuid.UUID
) -> Note | None:
    note = await get_note_by_id(db, user_id=user_id, note_id=note_id)
    if note is None:
        return None
    note.deleted_at = utcnow()
    await db.flush()
    return note


async def restore_note(
    db: AsyncSession, *, user_id: uuid.UUID, note_id: uuid.UUID
) -> Note | None:
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        return None
    note.deleted_at = None
    await db.flush()
    return note


async def list_notes(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    kind: NoteKind | None = None,
    source_type: NoteSourceType | None = None,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[Note]:
    query = select(Note).where(Note.user_id == user_id)

    if not include_deleted:
        query = query.where(Note.deleted_at.is_(None))

    if kind is not None:
        query = query.where(Note.kind == kind)

    if source_type is not None:
        query = query.where(Note.source_type == source_type)

    query = query.order_by(Note.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def count_notes(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    kind: NoteKind | None = None,
    source_type: NoteSourceType | None = None,
    include_deleted: bool = False,
) -> int:
    query = select(func.count()).select_from(Note).where(Note.user_id == user_id)

    if not include_deleted:
        query = query.where(Note.deleted_at.is_(None))

    if kind is not None:
        query = query.where(Note.kind == kind)

    if source_type is not None:
        query = query.where(Note.source_type == source_type)

    result = await db.execute(query)
    return result.scalar_one()


async def search_notes(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: KnowledgeSearchRequest,
) -> tuple[list[Note], int]:
    like = f"%{payload.q}%"
    query = select(Note).where(
        Note.user_id == user_id,
        Note.deleted_at.is_(None),
        or_(
            Note.title.ilike(like),
            Note.content.ilike(like),
            Note.tags.ilike(like),
        ),
    )

    if payload.kind is not None:
        query = query.where(Note.kind == payload.kind)

    count_query = select(func.count()).select_from(Note).where(
        Note.user_id == user_id,
        Note.deleted_at.is_(None),
        or_(
            Note.title.ilike(like),
            Note.content.ilike(like),
            Note.tags.ilike(like),
        ),
    )
    if payload.kind is not None:
        count_query = count_query.where(Note.kind == payload.kind)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = query.order_by(Note.created_at.desc())
    query = query.limit(payload.limit).offset(0)

    result = await db.execute(query)
    notes = list(result.scalars().all())
    return notes, total


async def create_note_link(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    source_note_id: uuid.UUID,
    target_note_id: uuid.UUID,
    link_type: str,
) -> NoteLink | None:
    if source_note_id == target_note_id:
        return None

    # Verify both notes belong to the user
    source = await get_note_by_id(db, user_id=user_id, note_id=source_note_id)
    target = await get_note_by_id(db, user_id=user_id, note_id=target_note_id)
    if source is None or target is None:
        return None

    # Linking twice is idempotent; the database enforces the unique edge.
    existing = await db.execute(
        select(NoteLink).where(
            NoteLink.source_note_id == source_note_id,
            NoteLink.target_note_id == target_note_id,
            NoteLink.link_type == link_type,
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    link = NoteLink(
        source_note_id=source_note_id,
        target_note_id=target_note_id,
        link_type=link_type,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def list_note_links(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> list[NoteLink]:
    # Verify the note belongs to the user
    note = await get_note_by_id(db, user_id=user_id, note_id=note_id)
    if note is None:
        return []

    result = await db.execute(
        select(NoteLink).where(
            (NoteLink.source_note_id == note_id)
            | (NoteLink.target_note_id == note_id)
        )
    )
    return list(result.scalars().all())


async def delete_note_link(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    link_id: uuid.UUID,
) -> NoteLink | None:
    # A link is visible only when both endpoints belong to the requesting user.
    user_note_ids = select(Note.id).where(Note.user_id == user_id)
    result = await db.execute(
        select(NoteLink).where(
            NoteLink.id == link_id,
            NoteLink.source_note_id.in_(user_note_ids),
            NoteLink.target_note_id.in_(user_note_ids),
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        return None

    await db.delete(link)
    await db.flush()
    return link
