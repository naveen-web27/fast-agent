"""Health endpoints for deployment monitoring."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.db.session import engine

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a liveness response without querying the database."""
    return {"status": "ok"}


@router.get("/health/db")
async def database_health_check() -> dict[str, str]:
    """Open a real connection and run SELECT 1, surfacing the raw driver error on failure."""
    if engine is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="DATABASE_URL is not configured")
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"[:500]
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail) from exc
    return {"status": "ok"}
