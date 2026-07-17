"""Domain-level exceptions for LINA entities."""

from __future__ import annotations


class EntityError(Exception):
    """Base exception for all entity/domain invariant violations."""


class InvalidStateTransitionError(EntityError):
    """Raised when an entity is asked to transition to an illegal state."""

    def __init__(self, entity: str, current: str, requested: str) -> None:
        self.entity = entity
        self.current = current
        self.requested = requested
        super().__init__(
            f"{entity}: cannot transition from '{current}' to '{requested}'"
        )


class ScopeViolationError(EntityError):
    """Raised when a target/action falls outside an engagement's authorized scope."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Scope violation: {detail}")


class EntityValidationError(EntityError):
    """Raised for entity-specific validation failures beyond Pydantic's schema checks."""