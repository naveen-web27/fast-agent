"""Minimal transactional email sending via the Resend HTTP API."""
import logging

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailNotConfiguredError(Exception):
    """Raised when RESEND_API_KEY is missing so callers can surface a clear error."""


class EmailDeliveryError(Exception):
    """Raised when Resend rejects the message or can't be reached."""


async def send_email(settings: Settings, *, to: str, subject: str, html: str) -> None:
    """Send a transactional email through Resend, raising on any failure."""
    if not settings.resend_api_key:
        logger.error("RESEND_API_KEY is not configured; cannot send email")
        raise EmailNotConfiguredError("RESEND_API_KEY is not configured")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": settings.resend_from_email, "to": [to], "subject": subject, "html": html},
            )
    except httpx.HTTPError as exc:
        logger.exception("Could not reach Resend")
        raise EmailDeliveryError("Email provider unreachable") from exc
    if response.is_error:
        # Resend's sandbox sender (onboarding@resend.dev) only delivers to the account owner's address.
        logger.error("Resend rejected email (%s): %s", response.status_code, response.text[:500])
        raise EmailDeliveryError(f"Email provider returned {response.status_code}")
