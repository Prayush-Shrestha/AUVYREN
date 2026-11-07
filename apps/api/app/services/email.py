"""Transactional email delivery.

Development can use a console adapter. Production configuration rejects it, so
reset links are never silently discarded outside local development. SMTP is
handled with the standard library off the event loop.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _mask_email(address: str) -> str:
    local, _, domain = address.partition("@")
    visible = local[:1] if local else ""
    return f"{visible}***@{domain}" if domain else "***"


class EmailService:
    async def send_password_reset(
        self,
        *,
        to_email: str,
        display_name: str | None,
        reset_url: str,
    ) -> None:
        settings = get_settings()
        if settings.email_provider == "console":
            # The reset link is intentionally visible only in local development.
            logger.warning(
                "Development password reset for %s: %s",
                _mask_email(to_email),
                reset_url,
            )
            return

        message = EmailMessage()
        message["Subject"] = "Reset your Auvyren password"
        message["From"] = settings.email_from
        message["To"] = to_email
        greeting = f"Hello {display_name}," if display_name else "Hello,"
        message.set_content(
            f"{greeting}\n\n"
            "A password reset was requested for your Auvyren account. "
            "This link is valid for 30 minutes and can be used once:\n\n"
            f"{reset_url}\n\n"
            "If you did not request this, you can safely ignore this email. "
            "Your current password remains unchanged.\n"
        )
        await asyncio.to_thread(self._send_smtp, message)

    def _send_smtp(self, message: EmailMessage) -> None:
        settings = get_settings()
        if not settings.smtp_host:
            raise RuntimeError("SMTP_HOST is not configured")

        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.ehlo()
            if settings.smtp_use_tls:
                smtp.starttls(context=context)
                smtp.ehlo()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)


email_service = EmailService()


async def send_password_reset_email(
    *,
    to_email: str,
    display_name: str | None,
    reset_url: str,
) -> None:
    """Background wrapper: delivery failures never reveal whether an account exists."""
    try:
        await email_service.send_password_reset(
            to_email=to_email,
            display_name=display_name,
            reset_url=reset_url,
        )
    except Exception:
        logger.exception("Password reset email delivery failed")
