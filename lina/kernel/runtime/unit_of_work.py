"""SQLAlchemy-backed Unit of Work adapter.

NOTE on import ordering: `SQLiteKnowledgeGraph` and `SQLAlchemyPromptRegistry`
are imported lazily inside `__aenter__` rather than at module top-level.
Both pull in `kernel.knowledge_graph.db.models` / `kernel.prompt_registry.db.models`,
which import `Base` from `kernel.runtime.db.base` — a submodule of this very
package. Importing them eagerly at module scope re-enters `kernel.runtime`
while its own `__init__.py` is still executing (via container.py -> this
module), causing a circular import. Deferring the import to call-time avoids
this without changing any public behavior: by the time a UnitOfWork is
actually used, `kernel.runtime` is always fully initialized.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kernel.ports.unit_of_work import UnitOfWork
from kernel.runtime.repositories.factory import (
    agent_session_repository,
    agent_step_repository,
    asset_repository,
    audit_entry_repository,
    credential_repository,
    engagement_repository,
    finding_repository,
    report_repository,
    target_repository,
    tool_execution_repository,
)

logger = structlog.get_logger(__name__)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """One transactional session exposing all entity repositories, plus the
    Knowledge Graph and Prompt Registry adapters, as attributes — all share
    the same underlying AsyncSession and therefore the same commit/rollback
    boundary.

    Usage:
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            await uow.engagements.add(engagement)
            await uow.knowledge_graph.upsert_node(node)
            await uow.commit()
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._committed = False

    async def __aenter__(self) -> Self:
        # Deferred imports — see module docstring for why these cannot be
        # module-level imports without triggering a circular import.
        from kernel.knowledge_graph.sqlite_adapter import SQLiteKnowledgeGraph
        from kernel.prompt_registry.sqlalchemy_adapter import SQLAlchemyPromptRegistry

        self._session = self._session_factory()
        self._committed = False

        self.engagements = engagement_repository(self._session)
        self.targets = target_repository(self._session)
        self.findings = finding_repository(self._session)
        self.assets = asset_repository(self._session)
        self.credentials = credential_repository(self._session)
        self.tool_executions = tool_execution_repository(self._session)
        self.agent_sessions = agent_session_repository(self._session)
        self.agent_steps = agent_step_repository(self._session)
        self.reports = report_repository(self._session)
        self.audit_entries = audit_entry_repository(self._session)

        self.knowledge_graph = SQLiteKnowledgeGraph(self._session)
        self.prompt_registry = SQLAlchemyPromptRegistry(self._session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc_type is not None:
                await self._session.rollback()
            elif not self._committed:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        assert self._session is not None, "commit() called outside an async-with block"
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        assert self._session is not None, "rollback() called outside an async-with block"
        await self._session.rollback()
        self._committed = False

    @property
    def session(self) -> AsyncSession:
        """Escape hatch for adapters/tests needing the raw session. Prefer the
        typed repository/knowledge_graph/prompt_registry attributes instead.
        """
        assert self._session is not None, "Unit of Work is not active."
        return self._session