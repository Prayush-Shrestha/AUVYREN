"""Knowledge workspace endpoints: notes, links, and search."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.session import get_db_session
from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    NoteCreate,
    NoteKind,
    NoteLinkCreate,
    NoteLinkResponse,
    NoteListResponse,
    NoteResponse,
    NoteSourceType,
    NoteUpdate,
)
from app.services.auth import CurrentAuth
from app.services.knowledge import (
    create_note,
    create_note_link,
    delete_note,
    delete_note_link,
    get_note_by_id,
    list_note_links,
    list_notes,
    restore_note,
    search_notes,
    update_note,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"], dependencies=[Depends(require_csrf)])


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a note",
)
async def create_note_endpoint(
    payload: NoteCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> NoteResponse:
    note = await create_note(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List notes",
)
async def list_notes_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    kind: NoteKind | None = Query(None),
    source_type: NoteSourceType | None = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> NoteListResponse:
    notes = await list_notes(
        db,
        user_id=auth.user.id,
        kind=kind,
        source_type=source_type,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    return NoteListResponse(notes=[NoteResponse.model_validate(n) for n in notes])


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a single note",
)
async def get_note_endpoint(
    note_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> NoteResponse:
    note = await get_note_by_id(db, user_id=auth.user.id, note_id=note_id)
    if note is None:
        raise AppError(
            404,
            "note_not_found",
            title="Note not found",
            detail="That note does not exist or has already been deleted.",
        )
    return NoteResponse.model_validate(note)


@router.patch(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
)
async def update_note_endpoint(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> NoteResponse:
    note = await update_note(db, user_id=auth.user.id, note_id=note_id, payload=payload)
    if note is None:
        raise AppError(
            404,
            "note_not_found",
            title="Note not found",
            detail="That note does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a note",
)
async def delete_note_endpoint(
    note_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    note = await delete_note(db, user_id=auth.user.id, note_id=note_id)
    if note is None:
        raise AppError(
            404,
            "note_not_found",
            title="Note not found",
            detail="That note does not exist or has already been deleted.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.post(
    "/{note_id}/restore",
    response_model=NoteResponse,
    summary="Restore a soft-deleted note",
)
async def restore_note_endpoint(
    note_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> NoteResponse:
    note = await restore_note(db, user_id=auth.user.id, note_id=note_id)
    if note is None:
        raise AppError(
            404,
            "note_not_found",
            title="Note not found",
            detail="That note does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


# Note links

@router.post(
    "/{note_id}/links",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a link between notes",
)
async def create_note_link_endpoint(
    note_id: uuid.UUID,
    payload: NoteLinkCreate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> NoteResponse:
    if str(payload.source_note_id) != str(note_id):
        raise AppError(
            400,
            "invalid_link",
            title="Invalid link",
            detail="Source note ID must match the note in the URL.",
        )
    if payload.source_note_id == payload.target_note_id:
        raise AppError(
            400,
            "invalid_link",
            title="Invalid link",
            detail="A note cannot link to itself.",
        )

    link = await create_note_link(
        db,
        user_id=auth.user.id,
        source_note_id=payload.source_note_id,
        target_note_id=payload.target_note_id,
        link_type=payload.link_type,
    )
    if link is None:
        raise AppError(
            404,
            "note_not_found",
            title="Note not found",
            detail="Source or target note not found.",
        )
    await db.commit()
    await db.refresh(link)
    note = await get_note_by_id(db, user_id=auth.user.id, note_id=note_id)
    return NoteResponse.model_validate(note)


@router.get(
    "/{note_id}/links",
    response_model=list[NoteLinkResponse],
    summary="List links for a note",
)
async def list_note_links_endpoint(
    note_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[NoteLinkResponse]:
    links = await list_note_links(db, user_id=auth.user.id, note_id=note_id)
    return [NoteLinkResponse.model_validate(link) for link in links]


@router.delete(
    "/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note link",
)
async def delete_note_link_endpoint(
    link_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    link = await delete_note_link(db, user_id=auth.user.id, link_id=link_id)
    if link is None:
        raise AppError(
            404,
            "link_not_found",
            title="Link not found",
            detail="That link does not exist.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


# Search

@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search notes",
)
async def search_notes_endpoint(
    payload: KnowledgeSearchRequest,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeSearchResponse:
    notes, total = await search_notes(db, user_id=auth.user.id, payload=payload)
    return KnowledgeSearchResponse(
        notes=[NoteResponse.model_validate(n) for n in notes],
        total=total,
    )
