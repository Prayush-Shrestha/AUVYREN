"""Privacy, consent, export, and deletion services (Phase 6).

Handles AI consent management, data export, account deletion, and audit logging
with full ownership enforcement and audit trails.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import constant_time_equals, hash_token
from app.db.models.privacy import (
    AccountDeletion,
    AIConsent,
    AuditEvent,
    DataExport,
)
from app.db.models.user import User
from app.schemas.privacy import (
    AccountDeletionCreate,
    AIConsentCreate,
    DataExportCreate,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# AI Consent management
# ---------------------------------------------------------------------------


async def get_consent(
    db: AsyncSession, *, user_id: uuid.UUID, provider: str
) -> AIConsent | None:
    result = await db.execute(
        select(AIConsent).where(
            AIConsent.user_id == user_id,
            AIConsent.provider == provider,
        )
    )
    return result.scalar_one_or_none()


async def create_or_update_consent(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: AIConsentCreate,
) -> AIConsent:
    consent = await get_consent(db, user_id=user_id, provider=payload.provider)
    if consent is None:
        consent = AIConsent(
            user_id=user_id,
            provider=payload.provider,
            policy_version=payload.policy_version or "1.0",
        )
        db.add(consent)

    consent.granted_at = utcnow()
    consent.revoked_at = None
    consent.policy_version = payload.policy_version or "1.0"

    await db.flush()
    await db.refresh(consent)
    return consent


async def revoke_consent(
    db: AsyncSession, *, user_id: uuid.UUID, provider: str
) -> AIConsent | None:
    consent = await get_consent(db, user_id=user_id, provider=provider)
    if consent is None:
        return None
    consent.revoked_at = utcnow()
    await db.flush()
    await db.refresh(consent)
    return consent


async def list_consents(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[AIConsent]:
    result = await db.execute(
        select(AIConsent).where(AIConsent.user_id == user_id).order_by(AIConsent.created_at.desc())
    )
    return list(result.scalars().all())


async def check_consent(
    db: AsyncSession, *, user_id: uuid.UUID, provider: str
) -> bool:
    consent = await get_consent(db, user_id=user_id, provider=provider)
    if consent is None:
        return False
    return consent.granted_at is not None and consent.revoked_at is None


# ---------------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------------


async def create_export(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: DataExportCreate,
) -> DataExport:
    export = DataExport(
        user_id=user_id,
        status="pending",
    )
    db.add(export)
    await db.flush()
    await db.refresh(export)
    return export


async def list_exports(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[DataExport]:
    result = await db.execute(
        select(DataExport)
        .where(DataExport.user_id == user_id)
        .order_by(DataExport.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_export(
    db: AsyncSession, *, user_id: uuid.UUID, export_id: uuid.UUID
) -> DataExport | None:
    result = await db.execute(
        select(DataExport).where(
            DataExport.id == export_id,
            DataExport.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Account deletion
# ---------------------------------------------------------------------------


async def request_account_deletion(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: AccountDeletionCreate,
    confirmation_token_hash: str,
) -> AccountDeletion:
    # A new request supersedes any older pending request without deleting data.
    await db.execute(
        update(AccountDeletion)
        .where(
            AccountDeletion.user_id == user_id,
            AccountDeletion.status == "pending",
        )
        .values(status="cancelled")
    )
    deletion = AccountDeletion(
        user_id=user_id,
        status="pending",
        confirmation_token=confirmation_token_hash,
        reason=payload.reason,
    )
    db.add(deletion)
    await db.flush()
    await db.refresh(deletion)
    return deletion


async def confirm_account_deletion(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    confirmation_token: str,
) -> AccountDeletion | None:
    result = await db.execute(
        select(AccountDeletion).where(
            AccountDeletion.user_id == user_id,
            AccountDeletion.status == "pending",
        )
    )
    deletion = result.scalar_one_or_none()
    if deletion is None or not deletion.confirmation_token:
        return None
    if not constant_time_equals(
        hash_token(confirmation_token), deletion.confirmation_token
    ):
        return None
    deletion.status = "confirmed"
    deletion.confirmed_at = utcnow()
    await db.flush()
    await db.refresh(deletion)
    return deletion


async def complete_account_deletion(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> bool:
    """Hard-delete the user and all associated data after confirmation."""
    result = await db.execute(
        select(AccountDeletion).where(
            AccountDeletion.user_id == user_id,
            AccountDeletion.status == "confirmed",
        )
    )
    deletion = result.scalar_one_or_none()
    if deletion is None:
        return False

    deletion.status = "completed"
    deletion.completed_at = utcnow()
    await db.flush()

    # Keep a user-independent audit trail after the account row is gone.
    await record_audit_event(
        db,
        user_id=None,
        event_type="account.deletion.completed",
        details=f"Account {user_id} deleted after confirmation.",
    )

    user = await db.get(User, user_id)
    if user is not None:
        await db.delete(user)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------


async def record_audit_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    event_type: str,
    details: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        event_type=event_type,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def list_audit_events(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    event_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditEvent]:
    query = select(AuditEvent)
    if user_id is not None:
        query = query.where(AuditEvent.user_id == user_id)
    if event_type is not None:
        query = query.where(AuditEvent.event_type == event_type)
    query = query.order_by(AuditEvent.created_at.desc())
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())
