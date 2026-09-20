"""Health endpoints for deployment monitoring."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a liveness response without querying the database."""
    return {"status": "ok"}