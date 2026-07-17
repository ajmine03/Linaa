"""AgentSession entity: tracks a running AI agent's lifecycle and context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from kernel.entities.base import BaseEntity, utcnow
from kernel.entities.enums import AgentSessionStatus
from kernel.entities.exceptions import InvalidStateTransitionError

_VALID_TRANSITIONS: dict[AgentSessionStatus, set[AgentSessionStatus]] = {
    AgentSessionStatus.INITIALIZING: {
        AgentSessionStatus.RUNNING,
        AgentSessionStatus.FAILED,
        AgentSessionStatus.ABORTED,
    },
    AgentSessionStatus.RUNNING: {
        AgentSessionStatus.WAITING_FOR_APPROVAL,
        AgentSessionStatus.WAITING_FOR_INPUT,
        AgentSessionStatus.COMPLETED,
        AgentSessionStatus.FAILED,
        AgentSessionStatus.ABORTED,
    },
    AgentSessionStatus.WAITING_FOR_APPROVAL: {
        AgentSessionStatus.RUNNING,
        AgentSessionStatus.ABORTED,
    },
    AgentSessionStatus.WAITING_FOR_INPUT: {
        AgentSessionStatus.RUNNING,
        AgentSessionStatus.ABORTED,
    },
    AgentSessionStatus.COMPLETED: set(),
    AgentSessionStatus.FAILED: set(),
    AgentSessionStatus.ABORTED: set(),
}


class AgentStep(BaseEntity):
    """A single reasoning/action step within an agent session (for replay/audit)."""

    agent_session_id: str
    step_index: int = Field(ge=0)
    thought: str | None = None
    action: str | None = None
    action_input: dict[str, Any] = Field(default_factory=dict)
    observation: str | None = None
    tool_execution_id: str | None = None

    _entity_name = "AgentStep"


class AgentSession(BaseEntity):
    """Tracks one end-to-end run of an agent (plugin agent or coding agent)."""

    engagement_id: str
    plugin_name: str
    agent_name: str
    status: AgentSessionStatus = Field(default=AgentSessionStatus.INITIALIZING)
    goal: str
    model_used: str | None = None
    max_steps: int = Field(default=50, ge=1, le=1000)
    current_step: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: datetime | None = None
    parent_session_id: str | None = Field(
        default=None, description="For sub-agents spawned by an orchestrator agent."
    )
    context_summary: str | None = None
    failure_reason: str | None = None

    _entity_name = "AgentSession"

    def transition_to(self, new_status: AgentSessionStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                self._entity_name, self.status.value, new_status.value
            )
        self.status = new_status
        if new_status in (
            AgentSessionStatus.COMPLETED,
            AgentSessionStatus.FAILED,
            AgentSessionStatus.ABORTED,
        ):
            self.ended_at = utcnow()
        self.touch()

    def increment_step(self) -> None:
        self.current_step += 1
        self.touch()

    @property
    def steps_remaining(self) -> int:
        return max(0, self.max_steps - self.current_step)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            AgentSessionStatus.COMPLETED,
            AgentSessionStatus.FAILED,
            AgentSessionStatus.ABORTED,
        )