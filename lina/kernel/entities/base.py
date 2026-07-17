"""Base entity primitives: identifiers, timestamps, and the root entity model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field


def new_id() -> str:
    """Generate a URL-safe unique entity identifier."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class EntityId(BaseModel):
    """Typed wrapper for entity identifiers to prevent primitive obsession."""

    value: str = Field(default_factory=new_id)

    model_config = ConfigDict(frozen=True)

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)


class BaseEntity(BaseModel):
    """Root class for all LINA domain entities.

    Provides identity, audit timestamps, and soft metadata. Entities are
    mutable within a bounded transaction but always validate on assignment.
    """

    id: str = Field(default_factory=new_id, description="Unique entity identifier (UUID4).")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    _entity_name: ClassVar[str] = "BaseEntity"

    def touch(self) -> None:
        """Update the `updated_at` timestamp — call after any mutation."""
        self.updated_at = utcnow()

    def with_metadata(self, **kwargs: Any) -> Self:
        """Return self after merging additional metadata (mutates in place)."""
        self.metadata.update(kwargs)
        self.touch()
        return self


class ValueObject(BaseModel):
    """Base class for immutable value objects (no identity, structural equality)."""

    model_config = ConfigDict(frozen=True, extra="forbid")