"""Privacy, consent, export, and deletion endpoints (Phase 6).

All endpoints require an authenticated session. Mutating routes require CSRF
validation. Cloud AI is not available in Phase 6; consent gates all AI access.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.models.privacy import AccountDeletion
from app.db.session import get_db_session
from app.schemas.privacy import (
    AccountDeletionCreate,
    AccountDeletionResponse,
    AIConsentCreate,
    AIConsentResponse,
    AuditEventResponse,
    DataExportCreate,
    DataExportResponse,
    ExportDownloadResponse,
)
from app.services.auth import CurrentAuth
from app.services.privacy import (
    check_consent,
    complete_account_deletion,
    create_export,
    create_or_update_consent,
    get_export,
    utcnow,
)
from app.services.privacy import (
    list_audit_events as list_audit_events_svc,
)
from app.services.privacy import (
    list_consents as list_consents_svc,
)
from app.services.privacy import (
    list_exports as list_exports_svc,
)
from app.services.privacy import (
    request_account_deletion as request_account_deletion_svc,
)
from app.services.privacy import (
    revoke_consent as revoke_consent_svc,
)

router = APIRouter(prefix="/privacy", tags=["Privacy"], dependencies=[Depends(require_csrf)])


# ---------------------------------------------------------------------------
# AI Consent
# ---------------------------------------------------------------------------


@router.get(
    "/consent",
    response_model=list[AIConsentResponse],
    summary="List AI consent settings",
)
async def list_consents(
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[AIConsentResponse]:
    consents = await list_consents_svc(db, user_id=auth.user.id)
    return [AIConsentResponse.model_validate(c) for c in consents]


@router.post(
    "/consent/{provider}",
    response_model=AIConsentResponse,
    summary="Grant or update AI provider consent",
)
async def create_consent_endpoint(
    provider: str,
    payload: AIConsentCreate,
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
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    consent = await revoke_consent_svc(db, user_id=auth.user.id, provider=provider)
    if consent is None:
        raise AppError(
            404,
            "consent_not_found",
            title="Consent not found",
            detail="No consent record found for this provider.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get(
    "/consent/{provider}/check",
    response_model=dict,
    summary="Check if AI provider consent is granted",
)
async def check_consent_endpoint(
    provider: str,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    granted = await check_consent(db, user_id=auth.user.id, provider=provider)
    return {"granted": granted, "provider": provider}


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
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> DataExportResponse:
    export = await create_export(db, user_id=auth.user.id, payload=payload)
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
    exports = await list_exports_svc(db, user_id=auth.user.id, limit=limit, offset=offset)
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
    response_model=AccountDeletionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request account deletion",
)
async def request_account_deletion_endpoint(
    payload: AccountDeletionCreate,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> AccountDeletionResponse:
    deletion = await request_account_deletion_svc(
        db, user_id=auth.user.id, payload=payload
    )
    await db.commit()
    await db.refresh(deletion)
    return AccountDeletionResponse.model_validate(deletion)


@router.post(
    "/account/delete/confirm",
    response_model=AccountDeletionResponse,
    summary="Confirm account deletion with token",
)
async def confirm_account_deletion_endpoint(
    confirmation_token: str,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> AccountDeletionResponse:
    result = await db.execute(
        select(AccountDeletion).where(
            AccountDeletion.user_id == auth.user.id,
            AccountDeletion.status == "pending",
        )
    )
    deletion = result.scalar_one_or_none()
    if deletion is None:
        raise AppError(
            404,
            "deletion_not_found",
            title="Deletion not found",
            detail="No pending deletion request found.",
        )
    if deletion.confirmation_token != confirmation_token:
        raise AppError(
            403,
            "invalid_confirmation_token",
            title="Invalid confirmation token",
            detail="The confirmation token is invalid or expired.",
        )
    deletion.confirmed_at = utcnow()
    await db.commit()
    await db.refresh(deletion)
    return AccountDeletionResponse.model_validate(deletion)


@router.post(
    "/account/delete/complete",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Complete account deletion (requires confirmed deletion)",
)
async def complete_account_deletion_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    result = await db.execute(
        select(AccountDeletion).where(
            AccountDeletion.user_id == auth.user.id,
            AccountDeletion.status == "confirmed",
        )
    )
    deletion = result.scalar_one_or_none()
    if deletion is None:
        raise AppError(
            404,
            "deletion_not_confirmed",
            title="Deletion not confirmed",
            detail="Account deletion must be confirmed before completion.",
        )
    await complete_account_deletion(db, user_id=auth.user.id)
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


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
    events = await list_audit_events_svc(
        db, user_id=auth.user.id, event_type=event_type, limit=limit, offset=offset
    )
    return [AuditEventResponse.model_validate(e) for e in events]
