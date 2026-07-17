"""Engagement entity: the authorization boundary for all LINA activity.

Every tool execution, agent action, and finding is scoped to an Engagement.
This is the root aggregate enforced by the Authorization Framework.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from kernel.entities.base import BaseEntity, ValueObject, utcnow
from kernel.entities.enums import EngagementStatus, EngagementType
from kernel.entities.exceptions import InvalidStateTransitionError, ScopeViolationError

_VALID_TRANSITIONS: dict[EngagementStatus, set[EngagementStatus]] = {
    EngagementStatus.DRAFT: {EngagementStatus.ACTIVE, EngagementStatus.CANCELLED},
    EngagementStatus.ACTIVE: {
        EngagementStatus.PAUSED,
        EngagementStatus.COMPLETED,
        EngagementStatus.CANCELLED,
    },
    EngagementStatus.PAUSED: {EngagementStatus.ACTIVE, EngagementStatus.CANCELLED},
    EngagementStatus.COMPLETED: set(),
    EngagementStatus.CANCELLED: set(),
}


class ScopeRule(ValueObject):
    """A single inclusion/exclusion rule defining authorized engagement scope.

    Patterns support exact match, CIDR notation (for IPs), and glob-style
    wildcards (for domains, e.g. '*.example.com'). Interpretation of the
    pattern is delegated to the AuthorizationFramework's ScopeMatcher.
    """

    pattern: str
    is_exclusion: bool = False
    note: str | None = None

    @field_validator("pattern")
    @classmethod
    def pattern_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Scope rule pattern must not be empty.")
        return v.strip()


class AuthorizationDocument(ValueObject):
    """Metadata proving authorization exists for this engagement (ROE, SOW, etc.)."""

    document_reference: str = Field(
        description="Reference/ID of the rules-of-engagement or authorization letter."
    )
    authorized_by: str
    valid_from: datetime
    valid_until: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "AuthorizationDocument":
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from.")
        return self

    def is_currently_valid(self, *, at: datetime | None = None) -> bool:
        moment = at or utcnow()
        if moment < self.valid_from:
            return False
        if self.valid_until is not None and moment > self.valid_until:
            return False
        return True


class Engagement(BaseEntity):
    """The top-level authorization and activity boundary in LINA.

    All targets, tool executions, agent sessions, and findings must
    reference an engagement_id. The AuthorizationFramework refuses to
    execute any action-capable tool without an ACTIVE, currently-valid
    engagement whose scope covers the requested target.
    """

    name: str
    engagement_type: EngagementType
    status: EngagementStatus = Field(default=EngagementStatus.DRAFT)
    client_name: str | None = None
    operator: str = Field(description="Identity of the human operator responsible.")
    authorization: AuthorizationDocument
    scope_rules: list[ScopeRule] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    _entity_name = "Engagement"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Engagement name must not be empty.")
        return v.strip()

    def transition_to(self, new_status: EngagementStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                self._entity_name, self.status.value, new_status.value
            )
        self.status = new_status
        if new_status == EngagementStatus.ACTIVE and self.started_at is None:
            self.started_at = utcnow()
        if new_status in (EngagementStatus.COMPLETED, EngagementStatus.CANCELLED):
            self.ended_at = utcnow()
        self.touch()

    def is_actionable(self, *, at: datetime | None = None) -> bool:
        """Whether action-capable tools may currently run under this engagement."""
        return (
            self.status == EngagementStatus.ACTIVE
            and self.authorization.is_currently_valid(at=at)
        )

    def require_actionable(self) -> None:
        if not self.is_actionable():
            raise ScopeViolationError(
                f"Engagement '{self.name}' ({self.id}) is not active/authorized "
                f"(status={self.status.value})."
            )

    def add_scope_rule(self, rule: ScopeRule) -> None:
        self.scope_rules.append(rule)
        self.touch()