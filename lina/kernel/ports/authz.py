"""Authorization Framework port — the single choke point every action-capable
tool execution and risky agent action must pass through.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from kernel.entities.enums import ToolRiskLevel


@dataclass(slots=True, frozen=True)
class AuthorizationRequest:
    engagement_id: str
    target_identifier: str | None
    tool_name: str
    plugin_name: str
    risk_level: ToolRiskLevel
    requested_by: str
    parameters_digest: str | None = None


@dataclass(slots=True, frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    requires_human_approval: bool = False
    approval_token: str | None = None


class AuthorizationPort(ABC):
    """Evaluates whether a requested tool/agent action is permitted given the
    engagement's status, authorization window, and scope rules.
    """

    @abstractmethod
    async def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision:
        """Core decision function. Must check (in order): engagement exists and
        is_actionable(), target falls within scope_rules (unless risk_level is
        READ_ONLY and unscoped read-only is permitted by config), and risk-level
        policy (e.g. HIGH/DESTRUCTIVE always requires human approval).
        """

    @abstractmethod
    async def record_human_approval(
        self, approval_token: str, approved_by: str, *, approved: bool
    ) -> AuthorizationDecision:
        """Resolve a pending human-in-the-loop approval request."""

    @abstractmethod
    async def is_in_scope(self, engagement_id: str, target_identifier: str) -> bool:
        """Pure scope-matching check against an engagement's ScopeRules."""