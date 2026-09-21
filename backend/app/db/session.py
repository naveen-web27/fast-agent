"""Async SQLAlchemy database session dependency."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

if settings.database_url:
    engine = create_async_engine(
        settings.database_url,
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