"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from kernel.config.schema import DatabaseConfig
from kernel.runtime.db.base import Base

logger = structlog.get_logger(__name__)


def create_engine(config: DatabaseConfig) -> AsyncEngine:
    return create_async_engine(
        config.url,
        echo=config.echo,
        pool_pre_ping=config.pool_pre_ping,
        connect_args={"timeout": config.connect_timeout_seconds},
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def init_db(engine: AsyncEngine) -> None:
    """Create all tables if they don't exist. Idempotent — safe on every startup.

    NOTE: `kernel.knowledge_graph.db.models` and `kernel.prompt_registry.db.models`
    declare ORM tables (kg_nodes, kg_edges, prompt_templates) that live outside
    the kernel.runtime package. They are otherwise only imported lazily inside
    `SQLAlchemyUnitOfWork.__aenter__` (to avoid a circular import back into
    kernel.runtime — see unit_of_work.py). Without the imports below, those
    tables would never be registered on `Base.metadata` before `create_all()`
    runs here, and would silently never get created. Importing them locally,
    right before `create_all()`, guarantees registration while preserving the
    same deferred-import pattern that avoids the circular import.
    """
    import kernel.knowledge_graph.db.models  # noqa: F401
    import kernel.prompt_registry.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("db.initialized", tables=list(Base.metadata.tables.keys()))


async def dispose_engine(engine: AsyncEngine) -> None:
    await engine.dispose()
    logger.info("db.engine_disposed")


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Standalone session context manager for one-off operations outside a UoW."""
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()