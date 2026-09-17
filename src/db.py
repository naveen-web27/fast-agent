"""Runtime SQLite setup for conversation history, ratings, products, and orders.

Tenant/client configuration is maintained separately in config/clients.csv.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings
from src.models import Base

settings = get_settings()

# Plug in / change the SQLite file location via DATABASE_URL env var (see .env.example).
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.split("///")[-1]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create tables if they don't exist yet (call on app startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency yielding a request-scoped AsyncSession."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    """Context manager for use outside FastAPI request handlers (e.g. background tasks)."""
    async with AsyncSessionLocal() as session:
        yield session
