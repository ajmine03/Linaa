"""Unit of Work port — atomic transaction boundary spanning multiple repositories."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self


class UnitOfWork(ABC):
    """Async context-manager transaction boundary.

    Usage:
        async with uow_factory() as uow:
            await uow.engagements.add(engagement)
            await uow.targets.add(target)
            await uow.commit()
        # auto-rollback on exception, no-op if already committed.
    """

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...