"""ToolExecution entity: an auditable record of a single tool invocation.

This is the atomic unit the Authorization Framework gates, the Tool Runtime
executes, and the audit log persists. Every effect a plugin has on the
outside world flows through a ToolExecution record.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from kernel.entities.base import BaseEntity, utcnow
from kernel.entities.enums import ToolExecutionStatus, ToolRiskLevel
from kernel.entities.exceptions import InvalidStateTransitionError

_VALID_TRANSITIONS: dict[ToolExecutionStatus, set[ToolExecutionStatus]] = {
    ToolExecutionStatus.PENDING: {
        ToolExecutionStatus.APPROVED,
        ToolExecutionStatus.DENIED,
        ToolExecutionStatus.CANCELLED,
    },
    ToolExecutionStatus.APPROVED: {
        ToolExecutionStatus.RUNNING,
        ToolExecutionStatus.CANCELLED,
    },
    ToolExecutionStatus.RUNNING: {
        ToolExecutionStatus.SUCCEEDED,
        ToolExecutionStatus.FAILED,
        ToolExecutionStatus.TIMED_OUT,
        ToolExecutionStatus.CANCELLED,
    },
    ToolExecutionStatus.DENIED: set(),
    ToolExecutionStatus.SUCCEEDED: set(),
    ToolExecutionStatus.FAILED: set(),
    ToolExecutionStatus.CANCELLED: set(),
    ToolExecutionStatus.TIMED_OUT: set(),
}


class ToolExecution(BaseEntity):
    """Full lifecycle record of one tool call, from request through result."""

    engagement_id: str
    target_id: str | None = None
    agent_session_id: str | None = None
    plugin_name: str
    tool_name: str
    risk_level: ToolRiskLevel
    status: ToolExecutionStatus = Field(default=ToolExecutionStatus.PENDING)
    parameters: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = Field(description="Agent ID, plugin ID, or 'operator'.")
    approved_by: str | None = None
    denial_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exit_code: int | None = None
    stdout_ref: str | None = Field(
        default=None, description="Reference to stored stdout (path or object key)."
    )
    stderr_ref: str | None = None
    result_summary: str | None = None
    error_message: str | None = None
    correlation_id: str | None = Field(
        default=None, description="Ties this execution to a workflow/agent step."
    )

    _entity_name = "ToolExecution"

    @model_validator(mode="after")
    def validate_risk_requires_approval(self) -> "ToolExecution":
        if self.risk_level != ToolRiskLevel.READ_ONLY and self.status not in (
            ToolExecutionStatus.PENDING,
            ToolExecutionStatus.DENIED,
        ):
            if self.approved_by is None and self.status not in (
                ToolExecutionStatus.CANCELLED,
            ):
                raise ValueError(
                    f"Non-read-only tool execution (risk={self.risk_level}) "
                    f"reached status={self.status} without an approved_by identity."
                )
        return self

    def transition_to(
        self,
        new_status: ToolExecutionStatus,
        *,
        approved_by: str | None = None,
        denial_reason: str | None = None,
    ) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                self._entity_name, self.status.value, new_status.value
            )
        self.status = new_status
        if new_status == ToolExecutionStatus.APPROVED:
            self.approved_by = approved_by
        if new_status == ToolExecutionStatus.DENIED:
            self.denial_reason = denial_reason
        if new_status == ToolExecutionStatus.RUNNING:
            self.started_at = utcnow()
        if new_status in (
            ToolExecutionStatus.SUCCEEDED,
            ToolExecutionStatus.FAILED,
            ToolExecutionStatus.TIMED_OUT,
            ToolExecutionStatus.CANCELLED,
        ):
            self.completed_at = utcnow()
        self.touch()

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()