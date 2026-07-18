"""SQLAlchemy-backed Unit of Work adapter."""

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
    """One transactional session exposing all entity repositories as attributes.

    Usage:
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            await uow.engagements.add(engagement)
            await uow.commit()
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._committed = False

    async def __aenter__(self) -> Self:
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