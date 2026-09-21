"""Async SQLAlchemy database session dependency."""
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

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
        # Supabase's pooler (pgbouncer, transaction mode) multiplexes many client
        # connections onto few backend sessions, so a SQLAlchemy-pooled asyncpg
        # connection can hit a backend that already has a same-named prepared
        # statement from a different client. NullPool + unique statement names
        # (per SQLAlchemy's asyncpg+pgbouncer docs) avoids that collision.
        poolclass=NullPool,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
        },
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