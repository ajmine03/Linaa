"""Generic repository port — the persistence contract for all entities.

Concrete adapters (e.g. SQLAlchemy-backed) implement this per-entity-type.
Kept generic to avoid boilerplate across Engagement/Target/Finding/etc.
repositories while still being fully typed via TypeVar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from kernel.entities.base import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)


class Repository(ABC, Generic[TEntity]):
    """Abstract CRUD + query contract for a single entity type."""

    @abstractmethod
    async def get(self, entity_id: str) -> TEntity | None:
        """Fetch by ID. Returns None if not found (callers decide whether to raise)."""

    @abstractmethod
    async def add(self, entity: TEntity) -> TEntity:
        """Persist a new entity. Raises ConflictError on duplicate ID."""

    @abstractmethod
    async def update(self, entity: TEntity) -> TEntity:
        """Persist changes to an existing entity. Raises NotFoundError if absent."""

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete by ID. Returns True if a row was deleted, False if absent."""

    @abstractmethod
    async def list(
        self,
        *,
        filters: dict[str, object] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = True,
    ) -> list[TEntity]:
        """List with basic filtering/pagination. Filters are field==value AND-ed."""

    @abstractmethod
    async def count(self, *, filters: dict[str, object] | None = None) -> int:
        """Count matching entities without loading them."""


class EngagementScopedRepository(Repository[TEntity], Generic[TEntity]):
    """Repository specialization for entities that always belong to an Engagement."""

    @abstractmethod
    async def list_by_engagement(
        self,
        engagement_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TEntity]:
        """List all entities of this type scoped to one engagement."""