"""PostgreSQL async engine & session factory.

Engine is created lazily to ensure it binds to the correct event loop,
which is critical for pytest-asyncio compatibility with asyncpg.
Uses NullPool to prevent connections from being shared across event loops.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from packages.common.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


# -- Lazy engine creation --

_engine = None
_session_factory = None


def get_engine():
    """Get or create the async engine (lazy singleton)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.postgres_dsn,
            echo=settings.debug,
            poolclass=NullPool,
        )
    return _engine


def get_session_factory():
    """Get or create the session factory (lazy singleton)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


def reset_engine():
    """Reset engine and session factory. Used in tests to avoid stale loop bindings."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield an async DB session with auto commit/rollback."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
