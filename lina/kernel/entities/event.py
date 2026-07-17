"""Domain Event entity: the payload shape published on the kernel Event Bus."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from kernel.entities.base import BaseEntity, ValueObject
from kernel.entities.enums import EventSeverity


class EventEnvelope(ValueObject):
    """Immutable wrapper published on the Event Bus. Not persisted as-is;
    the Memory Engine / audit log may choose to persist a copy.
    """

    event_type: str = Field(description="Dotted namespace, e.g. 'finding.created'.")
    source: str = Field(description="Plugin/component name that emitted the event.")
    severity: EventSeverity = Field(default=EventSeverity.INFO)
    engagement_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class AuditEntry(BaseEntity):
    """A persisted, append-only audit record — never mutated after creation."""

    engagement_id: str | None = None
    actor: str = Field(description="Identity responsible: operator, agent id, plugin id.")
    action: str = Field(description="Dotted action name, e.g. 'tool_execution.approved'.")
    target_ref: str | None = Field(default=None, description="ID of the entity acted upon.")
    detail: dict[str, Any] = Field(default_factory=dict)
    severity: EventSeverity = Field(default=EventSeverity.INFO)

    _entity_name = "AuditEntry"