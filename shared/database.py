"""Database configuration for Nexus."""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nexus:nexus_secret@localhost:5432/nexus",
)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+asyncpg://",
        1,
    )

# Pool settings - configurable for Supabase/managed databases with connection limits
# Supabase transaction pooler works best with smaller pool sizes
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "5"))

# Check if we're using pgbouncer (Render, Supabase, etc.)
# pgbouncer transaction pooling doesn't work with prepared statements or pool_pre_ping
DATABASE_USE_PGBOUNCER = os.getenv("DATABASE_USE_PGBOUNCER", "true").lower() == "true"

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ENVIRONMENT") == "development",
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    # pool_pre_ping doesn't work well with pgbouncer transaction pooling
    # It executes prepared statements that conflict with connection reuse
    pool_pre_ping=not DATABASE_USE_PGBOUNCER,
    connect_args={
        # Critical: Disable prepared statement cache for pgbouncer compatibility
        "statement_cache_size": 0,
        # Force server-side parameter status check off for pgbouncer
        "server_settings": {"jit": "off"} if DATABASE_USE_PGBOUNCER else {},
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
