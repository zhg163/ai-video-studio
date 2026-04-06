"""PostgreSQL async engine & session factory."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from packages.common.config import settings

engine = create_async_engine(
    settings.postgres_dsn,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency: yield an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
