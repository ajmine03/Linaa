"""Bidirectional mapping between Pydantic domain entities and ORM records."""

from __future__ import annotations

import json
from typing import Any, Protocol, TypeVar

from kernel.entities.base import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)


class _ORMRecordLike(Protocol):
    id: str
    data: str


def entity_to_record_kwargs(
    entity: BaseEntity, *, extra_columns: dict[str, Any]
) -> dict[str, Any]:
    """Build the kwargs dict needed to construct/update an ORM record from an entity.

    `extra_columns` supplies the denormalized SQL-filterable columns (e.g.
    status, severity) already extracted by the caller from the entity.

    `entity` is typed as `BaseEntity` (not the looser `BaseModel`) because
    `id`, `created_at`, and `updated_at` are guaranteed to exist there —
    every persisted domain entity in LINA is a `BaseEntity` subclass, so
    this reflects the actual contract rather than working around it.
    """
    payload = entity.model_dump(mode="json")
    base: dict[str, Any] = {
        "id": entity.id,
        "created_at": entity.created_at,
        "updated_at": entity.updated_at,
        "data": json.dumps(payload, separators=(",", ":")),
    }
    base.update(extra_columns)
    return base


def record_to_entity(record: _ORMRecordLike, entity_cls: type[TEntity]) -> TEntity:
    """Deserialize an ORM record's JSON payload back into a validated domain entity."""
    raw = json.loads(record.data)
    return entity_cls.model_validate(raw)