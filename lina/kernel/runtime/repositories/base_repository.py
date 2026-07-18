"""Generic SQLAlchemy repository implementing the Repository/EngagementScopedRepository ports."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from kernel.entities.base import BaseEntity
from kernel.ports.exceptions import ConflictError, NotFoundError
from kernel.ports.repository import EngagementScopedRepository
from kernel.runtime.db.base import EntityRecordMixin
from kernel.runtime.db.mappers import entity_to_record_kwargs, record_to_entity

TEntity = TypeVar("TEntity", bound=BaseEntity)
TRecord = TypeVar("TRecord", bound=EntityRecordMixin)


class SQLAlchemyRepository(
    EngagementScopedRepository[TEntity],
    Generic[TEntity, TRecord],
):
    """Concrete repository backed by one SQLAlchemy ORM table per entity type."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        entity_cls: type[TEntity],
        record_cls: type[TRecord],
        column_extractor: Callable[[TEntity], dict[str, Any]],
    ) -> None:
        self._session = session
        self._entity_cls = entity_cls
        self._record_cls = record_cls
        self._column_extractor = column_extractor
        self._entity_name = entity_cls.__name__

    async def get(self, entity_id: str) -> TEntity | None:
        record = await self._session.get(
            self._record_cls,
            entity_id,
        )

        if record is None:
            return None

        return record_to_entity(
            record,
            self._entity_cls,
        )

    async def add(self, entity: TEntity) -> TEntity:
        existing = await self._session.get(
            self._record_cls,
            entity.id,
        )

        if existing is not None:
            raise ConflictError(
                f"{self._entity_name} with id={entity.id} already exists."
            )

        kwargs = entity_to_record_kwargs(
            entity,
            extra_columns=self._column_extractor(entity),
        )

        record = self._record_cls(**kwargs)

        self._session.add(record)
        await self._session.flush()

        return entity

    async def update(self, entity: TEntity) -> TEntity:
        record = await self._session.get(
            self._record_cls,
            entity.id,
        )

        if record is None:
            raise NotFoundError(
                self._entity_name,
                entity.id,
            )

        kwargs = entity_to_record_kwargs(
            entity,
            extra_columns=self._column_extractor(entity),
        )

        for key, value in kwargs.items():
            setattr(record, key, value)

        await self._session.flush()

        return entity

    async def delete(self, entity_id: str) -> bool:
        record = await self._session.get(
            self._record_cls,
            entity_id,
        )

        if record is None:
            return False

        await self._session.delete(record)
        await self._session.flush()

        return True

    async def list(
        self,
        *,
        filters: dict[str, object] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = True,
    ) -> builtins.list[TEntity]:
        stmt: Select[tuple[TRecord]] = select(
            self._record_cls
        )

        stmt = self._apply_sql_filters(
            stmt,
            filters or {},
        )

        stmt = self._apply_ordering(
            stmt,
            order_by,
            descending,
        )

        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)

        records = result.scalars().all()

        entities = [
            record_to_entity(
                record,
                self._entity_cls,
            )
            for record in records
        ]

        return self._apply_python_filters(
            entities,
            filters or {},
        )

    async def count(
        self,
        *,
        filters: dict[str, object] | None = None,
    ) -> int:
        stmt: Select[Any] = select(
            func.count()
        ).select_from(
            self._record_cls
        )

        stmt = self._apply_sql_filters(
            stmt,
            filters or {},
        )

        result = await self._session.execute(stmt)

        return int(result.scalar_one())

    async def list_by_engagement(
        self,
        engagement_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[TEntity]:
        if "engagement_id" not in self._sql_column_names():
            raise AttributeError(
                f"{self._record_cls.__name__} has no engagement_id column; "
                "this repository is not engagement-scoped."
            )

        return await self.list(
            filters={
                "engagement_id": engagement_id,
            },
            limit=limit,
            offset=offset,
        )

    def _apply_sql_filters(
        self,
        stmt: Select[Any],
        filters: dict[str, object],
    ) -> Select[Any]:
        column_names = self._sql_column_names()

        for key, value in filters.items():
            if key not in column_names:
                continue

            column: InstrumentedAttribute[Any] = getattr(
                self._record_cls,
                key,
            )

            stmt = stmt.where(
                column == value
            )

        return stmt

    def _apply_python_filters(
        self,
        entities: builtins.list[TEntity],
        filters: dict[str, object],
    ) -> builtins.list[TEntity]:
        """Apply filters that do not map to SQL columns in memory."""

        remaining = {
            key: value
            for key, value in filters.items()
            if key not in self._sql_column_names()
        }

        if not remaining:
            return entities

        return [
            entity
            for entity in entities
            if all(
                getattr(
                    entity,
                    key,
                    None,
                ) == value
                for key, value in remaining.items()
            )
        ]

    def _sql_column_names(self) -> set[str]:
        mapper = inspect(self._record_cls)

        if mapper is None:
            return set()

        return set(
            mapper.columns.keys()
        )

    def _apply_ordering(
        self,
        stmt: Select[Any],
        order_by: str | None,
        descending: bool,
    ) -> Select[Any]:
        column_name = order_by or "updated_at"

        if column_name not in self._sql_column_names():
            return stmt

        column: InstrumentedAttribute[Any] = getattr(
            self._record_cls,
            column_name,
        )

        return stmt.order_by(
            column.desc()
            if descending
            else column.asc()
        )