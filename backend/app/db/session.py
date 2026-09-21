"""Async SQLAlchemy database session dependency."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()


def _as_asyncpg_url(url: str) -> str:
    """Force the asyncpg driver even if DATABASE_URL was copied without it."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


if settings.database_url:
    engine = create_async_engine(
        _as_asyncpg_url(settings.database_url),
        pool_pre_ping=True,
        # Supabase's pooler (pgbouncer, transaction mode) doesn't support asyncpg's
        # prepared-statement cache; disabling it keeps the driver compatible with
        # both the pooler and a direct connection.
        connect_args={"statement_cache_size": 0},
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
else:
    engine = None
    SessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped database session when DATABASE_URL is configured."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    async with SessionLocal() as session:
        yield session