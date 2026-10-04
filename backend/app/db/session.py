"""Async SQLAlchemy database session dependency."""
import uuid
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
    # Transaction-mode pooler (port 6543) can hand each transaction a different backend, so nothing
    # may be cached and statement names must be unique. Session mode (5432) keeps one backend per
    # connection, so DB_STATEMENT_CACHE=true can reuse prepared statements and save a round trip per query.
    cache_args = (
        {}
        if settings.db_statement_cache
        else {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
        }
    )
    engine = create_async_engine(
        _as_asyncpg_url(settings.database_url),
        # Opening a new TLS connection to Supabase is slow, so keep a small pool.
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=cache_args,
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