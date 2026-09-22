"""HTTP endpoints for browsing live marketplace profiles."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.marketplace.schemas import ProfileDetail, ProfileListResponse
from app.features.marketplace.service import get_profile_detail, search_profiles

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


@router.get("/profiles/{profile_id}", response_model=ProfileDetail)
async def get_profile(profile_id: UUID, session: AsyncSession = Depends(get_db)) -> ProfileDetail:
    """Return the full profile detail, including reviews, for the profile preview page."""
    detail = await get_profile_detail(session, profile_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return detail
