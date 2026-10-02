"""Supabase access-token verification for protected API routes."""
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

SUSPENDED_DETAIL = "Your account has been suspended. Please contact support at rightconnect.co@gmail.com."


async def get_current_auth_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db),
) -> UUID:
    """Validate a Supabase access token and return its verified auth user ID; blocked accounts get 403."""
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured",
        )
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")

    headers = {
        "apikey": settings.supabase_publishable_key,
        "Authorization": f"Bearer {credentials.credentials}",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/user", headers=headers)

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    try:
        auth_user_id = UUID(response.json()["id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth user response") from exc

    blocked_at = await session.scalar(
        select(User.blocked_at).where(User.auth_user_id == auth_user_id, User.deleted_at.is_(None))
    )
    if blocked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SUSPENDED_DETAIL)
    return auth_user_id