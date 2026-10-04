"""Supabase access-token verification for protected API routes."""
import hashlib
import time
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

# Verified tokens are trusted for a short while so each API call doesn't wait on Supabase.
TOKEN_CACHE_SECONDS = 60
TOKEN_CACHE_MAX = 5000
_token_cache: dict[str, tuple[UUID, float]] = {}
_http_client: httpx.AsyncClient | None = None


async def _verify_with_supabase(settings: Settings, token: str) -> UUID:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10)
    response = await _http_client.get(
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
        headers={"apikey": settings.supabase_publishable_key, "Authorization": f"Bearer {token}"},
    )
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    try:
        return UUID(response.json()["id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth user response") from exc


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

    cache_key = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    now = time.monotonic()
    cached = _token_cache.get(cache_key)
    if cached is not None and cached[1] > now:
        # Already passed the blocked check below; a new block takes effect within TOKEN_CACHE_SECONDS.
        return cached[0]

    auth_user_id = await _verify_with_supabase(settings, credentials.credentials)
    blocked_at = await session.scalar(
        select(User.blocked_at).where(User.auth_user_id == auth_user_id, User.deleted_at.is_(None))
    )
    if blocked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SUSPENDED_DETAIL)
    if len(_token_cache) >= TOKEN_CACHE_MAX:
        _token_cache.clear()
    _token_cache[cache_key] = (auth_user_id, now + TOKEN_CACHE_SECONDS)
    return auth_user_id