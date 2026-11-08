"""Knowledge workspace service: notes, links, and search."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import Note, NoteKind, NoteLink, NoteSourceType
from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    NoteCreate,
    NoteUpdate,
)


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


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
        source_id=payload.source_id,
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
    # Verify both notes belong to the user
    source = await get_note_by_id(db, user_id=user_id, note_id=source_note_id)
    target = await get_note_by_id(db, user_id=user_id, note_id=target_note_id)
    if source is None or target is None:
        return None

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
    # Verify the note belongs to the user
    result = await db.execute(
        select(NoteLink).join(Note).where(
            NoteLink.id == link_id,
            Note.user_id == user_id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        return None

    await db.delete(link)
    await db.flush()
    return link
