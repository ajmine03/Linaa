"""Bidirectional mapping between Pydantic domain entities and ORM records."""

from __future__ import annotations

import json
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from kernel.runtime.db.base import EntityRecordMixin

TEntity = TypeVar("TEntity", bound=BaseModel)


class _ORMRecordLike(Protocol):
    id: str
    data: str


def entity_to_record_kwargs(entity: BaseModel, *, extra_columns: dict[str, Any]) -> dict[str, Any]:
    """Build the kwargs dict needed to construct/update an ORM record from an entity.

    `extra_columns` supplies the denormalized SQL-filterable columns (e.g.
    status, severity) already extracted by the caller from the entity.
    """
    payload = entity.model_dump(mode="json")
    base = {
        "id": payload["id"],
        "created_at": entity.created_at if hasattr(entity, "created_at") else payload["created_at"],  # type: ignore[attr-defined]
        "updated_at": entity.updated_at if hasattr(entity, "updated_at") else payload["updated_at"],  # type: ignore[attr-defined]
        "data": json.dumps(payload, separators=(",", ":")),
    }
    base.update(extra_columns)
    return base


def record_to_entity(record: _ORMRecordLike, entity_cls: type[TEntity]) -> TEntity:
    """Deserialize an ORM record's JSON payload back into a validated domain entity."""
    raw = json.loads(record.data)
    return entity_cls.model_validate(raw)