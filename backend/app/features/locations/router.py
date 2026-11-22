"""Public place-name lookup for the location picker."""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.locations.service import Place, places_for_pincode, search_places

router = APIRouter()


@router.get("/search", response_model=list[Place])
async def search(q: str = Query(min_length=1, max_length=60), session: AsyncSession = Depends(get_db)) -> list[Place]:
    """Areas matching a place name (area, taluk or district, typo tolerant) or the start of a PIN code."""
    return await search_places(session, q)


@router.get("/{pincode}", response_model=list[Place])
async def pincode_areas(
    pincode: str = Path(pattern=r"^[1-9][0-9]{5}$"), session: AsyncSession = Depends(get_db)
) -> list[Place]:
    """Every area under one PIN code (empty if the PIN isn't in the directory)."""
    return await places_for_pincode(session, pincode)
