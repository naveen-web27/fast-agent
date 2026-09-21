"""Minimal transactional email sending via the Resend HTTP API."""
import httpx

from app.core.config import Settings


class EmailNotConfiguredError(Exception):
    """Raised when RESEND_API_KEY is missing so callers can surface a clear error."""


async def send_email(settings: Settings, *, to: str, subject: str, html: str) -> None:
    """Send a transactional email through Resend, raising on any failure."""
    if not settings.resend_api_key:
        raise EmailNotConfiguredError("RESEND_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.resend_from_email, "to": [to], "subject": subject, "html": html},
        )
    response.raise_for_status()
