"""HTTP endpoints for browsing live marketplace profiles."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.marketplace.schemas import ProfileListResponse
from app.features.marketplace.service import search_profiles

router = APIRouter()


@router.get("/profiles", response_model=ProfileListResponse)
async def list_profiles(
    q: str | None = Query(default=None, description="Free-text search across name and headline"),
    city: str | None = Query(default=None),
    kind: str | None = Query(default=None, pattern="^(expert|company)$"),
    session: AsyncSession = Depends(get_db),
) -> ProfileListResponse:
    """Search verified experts and companies stored in the database."""
    return await search_profiles(session, query=q, city=city, kind=kind)
