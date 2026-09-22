"""HTTP endpoints for browsing live marketplace profiles."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.marketplace.schemas import ProfileDetail, ProfileListResponse
from app.features.marketplace.service import (
    IdentityNotFoundError,
    ProfileNotFoundError,
    get_profile_detail,
    list_saved_profiles,
    save_profile,
    search_profiles,
    unsave_profile,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


@router.get("/profiles", response_model=ProfileListResponse)
async def list_profiles(
    q: str | None = Query(default=None, description="Free-text search across name and headline"),
    city: str | None = Query(default=None),
    kind: str | None = Query(default=None, pattern="^(expert|company)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
) -> ProfileListResponse:
    """Search verified experts and companies stored in the database."""
    return await search_profiles(session, query=q, city=city, kind=kind, page=page, page_size=page_size)


@router.get("/profiles/saved", response_model=ProfileListResponse)
async def get_saved_profiles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ProfileListResponse:
    """Return the caller's bookmarked profiles for the Saved tab."""
    try:
        return await list_saved_profiles(session, auth_user_id, page=page, page_size=page_size)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/profiles/{profile_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def save_profile_endpoint(
    profile_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Bookmark a profile so the caller can find it again in Saved."""
    try:
        await save_profile(session, auth_user_id, profile_id)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/profiles/{profile_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_profile_endpoint(
    profile_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Remove a profile bookmark."""
    try:
        await unsave_profile(session, auth_user_id, profile_id)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/profiles/{profile_id}", response_model=ProfileDetail)
async def get_profile(profile_id: UUID, session: AsyncSession = Depends(get_db)) -> ProfileDetail:
    """Return the full profile detail, including reviews, for the profile preview page."""
    detail = await get_profile_detail(session, profile_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return detail
