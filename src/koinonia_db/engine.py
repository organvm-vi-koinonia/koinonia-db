"""Async engine factory and session management for koinonia-db."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_database_url() -> str:
    """Read DATABASE_URL from environment, converting to async driver if needed."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    # Convert postgresql:// to postgresql+psycopg:// for async
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


_engine: AsyncEngine | None = None


def get_engine(url: str | None = None, **kwargs) -> AsyncEngine:
    """Create or return the singleton async engine."""
    global _engine
    if _engine is None:
        db_url = url or get_database_url()
        _engine = create_async_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            echo=os.environ.get("DB_ECHO", "").lower() == "true",
            **kwargs,
        )
    return _engine


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine."""
    eng = engine or get_engine()
    return async_sessionmaker(eng, expire_on_commit=False)


async def dispose_engine() -> None:
    """Dispose the singleton engine (for clean shutdown)."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
