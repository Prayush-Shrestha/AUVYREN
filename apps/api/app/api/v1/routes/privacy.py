"""Privacy, consent, export, and deletion endpoints.

All endpoints require an authenticated session. Mutating routes require CSRF
validation. Cloud AI is not available; consent gates all provider access.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.core.cookies import clear_csrf_cookie, clear_session_cookie
from app.core.security import generate_token, hash_token
from app.db.session import get_db_session
from app.schemas.privacy import (
    AccountDeletionConfirmRequest,
    AccountDeletionCreate,
    AccountDeletionRequestResponse,
    AccountDeletionResponse,
    AIConsentCreate,
    AIConsentResponse,
    AuditEventResponse,
    ConsentCheckResponse,
    DataExportCreate,
    DataExportResponse,
    ExportDownloadResponse,
)
from app.services.auth import CurrentAuth, request_metadata
from app.services.privacy import (
    check_consent,
    complete_account_deletion,
    confirm_account_deletion,
    create_export,
    create_or_update_consent,
    get_export,
    list_audit_events,
    list_consents,
    list_exports,
    record_audit_event,
    request_account_deletion,
    revoke_consent,
)

router = APIRouter(prefix="/privacy", tags=["Privacy"], dependencies=[Depends(require_csrf)])


async def _audit(
    db: AsyncSession,
    request: Request,
    auth: CurrentAuth,
    event_type: str,
    details: str,
) -> None:
    user_agent, ip_address = request_metadata(request)
    await record_audit_event(
        db,
        user_id=auth.user.id,
        event_type=event_type,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ---------------------------------------------------------------------------
# AI Consent
# ---------------------------------------------------------------------------


@router.get(
    "/consent",
    response_model=list[AIConsentResponse],
    summary="List AI consent settings",
)
async def list_consents_endpoint(
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[AIConsentResponse]:
    consents = await list_consents(db, user_id=auth.user.id)
    return [AIConsentResponse.model_validate(c) for c in consents]


@router.post(
    "/consent/{provider}",
    response_model=AIConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant or update AI provider consent",
)
async def create_consent_endpoint(
    provider: str,
    payload: AIConsentCreate,
    request: Request,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> AIConsentResponse:
    if provider != payload.provider:
        raise AppError(
            400,
            "provider_mismatch",
            title="Provider mismatch",
            detail="Provider in URL does not match body.",
        )
    consent = await create_or_update_consent(db, user_id=auth.user.id, payload=payload)
    await _audit(db, request, auth, "ai.consent.granted", f"provider={provider}")
    await db.commit()
    await db.refresh(consent)
    return AIConsentResponse.model_validate(consent)


@router.delete(
    "/consent/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke AI provider consent",
)
async def revoke_consent_endpoint(
    provider: str,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    consent = await revoke_consent(db, user_id=auth.user.id, provider=provider)
    if consent is None:
        raise AppError(
            404,
            "consent_not_found",
            title="Consent not found",
            detail="No consent record found for this provider.",
        )
    await _audit(db, request, auth, "ai.consent.revoked", f"provider={provider}")
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get(
    "/consent/{provider}/check",
    response_model=ConsentCheckResponse,
    summary="Check if AI provider consent is granted",
)
async def check_consent_endpoint(
    provider: str,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ConsentCheckResponse:
    granted = await check_consent(db, user_id=auth.user.id, provider=provider)
    return ConsentCheckResponse(granted=granted, provider=provider)


# ---------------------------------------------------------------------------
# Data Export
# ---------------------------------------------------------------------------


@router.post(
    "/export",
    response_model=DataExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a data export",
)
async def create_export_endpoint(
    payload: DataExportCreate,
    request: Request,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> DataExportResponse:
    export = await create_export(db, user_id=auth.user.id, payload=payload)
    await _audit(db, request, auth, "data.export.requested", f"export_id={export.id}")
    await db.commit()
    await db.refresh(export)
    return DataExportResponse.model_validate(export)


@router.get(
    "/export",
    response_model=list[DataExportResponse],
    summary="List data exports",
)
async def list_exports_endpoint(
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[DataExportResponse]:
    exports = await list_exports(db, user_id=auth.user.id, limit=limit, offset=offset)
    return [DataExportResponse.model_validate(e) for e in exports]


@router.get(
    "/export/{export_id}",
    response_model=DataExportResponse,
    summary="Get a data export",
)
async def get_export_endpoint(
    export_id: uuid.UUID,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> DataExportResponse:
    export = await get_export(db, user_id=auth.user.id, export_id=export_id)
    if export is None:
        raise AppError(
            404,
            "export_not_found",
            title="Export not found",
            detail="That export does not exist or is not accessible.",
        )
    return DataExportResponse.model_validate(export)


@router.get(
    "/export/{export_id}/download",
    response_model=ExportDownloadResponse,
    summary="Download a data export",
)
async def download_export_endpoint(
    export_id: uuid.UUID,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ExportDownloadResponse:
    export = await get_export(db, user_id=auth.user.id, export_id=export_id)
    if export is None:
        raise AppError(
            404,
            "export_not_found",
            title="Export not found",
            detail="That export does not exist or is not accessible.",
        )
    if export.status != "completed":
        raise AppError(
            400,
            "export_not_ready",
            title="Export not ready",
            detail="The export has not completed yet.",
        )
    return ExportDownloadResponse(
        download_url=f"/api/v1/privacy/export/{export_id}/download",
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )


# ---------------------------------------------------------------------------
# Account Deletion
# ---------------------------------------------------------------------------


@router.post(
    "/account/delete",
    response_model=AccountDeletionRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request account deletion",
)
async def request_account_deletion_endpoint(
    payload: AccountDeletionCreate,
    request: Request,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> AccountDeletionRequestResponse:
    raw_token = generate_token()
    deletion = await request_account_deletion(
        db,
        user_id=auth.user.id,
        payload=payload,
        confirmation_token_hash=hash_token(raw_token),
    )
    await _audit(db, request, auth, "account.deletion.requested", f"deletion_id={deletion.id}")
    await db.commit()
    await db.refresh(deletion)
    base = AccountDeletionResponse.model_validate(deletion)
    return AccountDeletionRequestResponse(
        **base.model_dump(),
        confirmation_token=raw_token,
    )


@router.post(
    "/account/delete/confirm",
    response_model=AccountDeletionResponse,
    summary="Confirm account deletion with token",
)
async def confirm_account_deletion_endpoint(
    payload: AccountDeletionConfirmRequest,
    request: Request,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> AccountDeletionResponse:
    deletion = await confirm_account_deletion(
        db,
        user_id=auth.user.id,
        confirmation_token=payload.confirmation_token,
    )
    if deletion is None:
        raise AppError(
            400,
            "invalid_confirmation_token",
            title="Invalid confirmation token",
            detail="The confirmation token is invalid or no pending deletion exists.",
        )
    await _audit(db, request, auth, "account.deletion.confirmed", f"deletion_id={deletion.id}")
    await db.commit()
    await db.refresh(deletion)
    return AccountDeletionResponse.model_validate(deletion)


@router.post(
    "/account/delete/complete",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Complete account deletion (requires confirmed deletion)",
)
async def complete_account_deletion_endpoint(
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    completed = await complete_account_deletion(db, user_id=auth.user.id)
    if not completed:
        raise AppError(
            404,
            "deletion_not_confirmed",
            title="Deletion not confirmed",
            detail="Account deletion must be confirmed before completion.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    clear_session_cookie(response)
    clear_csrf_cookie(response)


# ---------------------------------------------------------------------------
# Audit Events
# ---------------------------------------------------------------------------


@router.get(
    "/audit",
    response_model=list[AuditEventResponse],
    summary="List audit events",
)
async def list_audit_events_endpoint(
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    event_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[AuditEventResponse]:
    events = await list_audit_events(
        db, user_id=auth.user.id, event_type=event_type, limit=limit, offset=offset
    )
    return [AuditEventResponse.model_validate(e) for e in events]
