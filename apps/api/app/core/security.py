"""Password, token and CSRF primitives.

Only hashes are persisted. Raw session and password-reset tokens exist in
memory, cookies and outbound email; they are never written to the database.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import uuid

from pwdlib import PasswordHash

from app.core.config import get_settings

_password_hash = PasswordHash.recommended()

# A valid hash used to keep invalid-email and invalid-password login paths
# similarly expensive.
_DUMMY_PASSWORD_HASH = _password_hash.hash("auvyren-dummy-password-value")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


async def hash_password_async(password: str) -> str:
    return await asyncio.to_thread(hash_password, password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


async def verify_password_async(password: str, password_hash: str) -> bool:
    return await asyncio.to_thread(verify_password, password, password_hash)


async def perform_dummy_password_check(password: str) -> None:
    await verify_password_async(password, _DUMMY_PASSWORD_HASH)


def generate_token() -> str:
    """Return a 256-bit URL-safe opaque token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def _csrf_signature(payload: str) -> str:
    key = get_settings().secret_key.encode("utf-8")
    return hmac.new(key, f"auvyren:csrf:{payload}".encode(), hashlib.sha256).hexdigest()


def issue_csrf_token(session_id: uuid.UUID | None) -> str:
    """Create a signed CSRF token bound to a session, or to an anonymous client."""
    subject = session_id.hex if session_id else "anon"
    nonce = generate_token()
    payload = f"v1.{subject}.{nonce}"
    return f"{payload}.{_csrf_signature(payload)}"


def verify_csrf_signature(token: str) -> str | None:
    """Validate token integrity and return its subject, or ``None`` if invalid."""
    try:
        version, subject, nonce, signature = token.split(".")
    except ValueError:
        return None
    if version != "v1" or len(nonce) < 20:
        return None
    payload = f"{version}.{subject}.{nonce}"
    if not constant_time_equals(signature, _csrf_signature(payload)):
        return None
    if subject != "anon":
        try:
            uuid.UUID(hex=subject)
        except ValueError:
            return None
    return subject


def csrf_subject_matches(token: str, session_id: uuid.UUID | None) -> bool:
    subject = verify_csrf_signature(token)
    expected = session_id.hex if session_id else "anon"
    return subject == expected
