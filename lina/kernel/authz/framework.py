"""Concrete AuthorizationFramework — implements AuthorizationPort.

This is the single mandatory choke point. Evaluation order:
  1. Engagement must exist.
  2. Engagement must be ACTIVE and within its authorization validity window.
  3. If a target is specified and risk_level is not READ_ONLY (or config
     disallows unscoped read-only), the target must match an in-scope rule.
  4. Risk-level policy determines auto-approve vs human-approval-required.

No caller may bypass this — the Tool Runtime invokes it unconditionally
before every non-trivial tool execution.
"""

from __future__ import annotations

import hashlib
import json

import structlog

from kernel.authz.pending_approvals import PendingApprovalStore
from kernel.authz.policy import RiskPolicy
from kernel.authz.scope_matcher import ScopeMatcher
from kernel.config.schema import AuthzConfig
from kernel.entities.engagement import Engagement
from kernel.ports.authz import AuthorizationDecision, AuthorizationPort, AuthorizationRequest
from kernel.ports.repository import Repository

logger = structlog.get_logger(__name__)


def digest_parameters(parameters: dict[str, object]) -> str:
    """Deterministic digest of tool parameters for audit correlation, without
    persisting raw (potentially sensitive) parameter values in decision logs.
    """
    encoded = json.dumps(parameters, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


class AuthorizationFramework(AuthorizationPort):
    def __init__(
        self,
        engagement_repository: Repository[Engagement],
        *,
        config: AuthzConfig,
        risk_policy: RiskPolicy | None = None,
        scope_matcher: ScopeMatcher | None = None,
        pending_approvals: PendingApprovalStore | None = None,
    ) -> None:
        self._engagements = engagement_repository
        self._config = config
        self._risk_policy = risk_policy or RiskPolicy()
        self._scope_matcher = scope_matcher or ScopeMatcher()
        self._pending = pending_approvals or PendingApprovalStore()

    async def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision:
        engagement = await self._engagements.get(request.engagement_id)
        if engagement is None:
            decision = AuthorizationDecision(
                allowed=False, reason=f"Engagement {request.engagement_id} does not exist."
            )
            self._log_decision(request, decision)
            return decision

        if not engagement.is_actionable():
            decision = AuthorizationDecision(
                allowed=False,
                reason=f"Engagement is not active/authorized (status={engagement.status.value}).",
            )
            self._log_decision(request, decision)
            return decision

        is_read_only = self._risk_policy.is_read_only(request.risk_level)
        skip_scope_check = is_read_only and self._config.allow_unscoped_read_only_tools

        if request.target_identifier and self._config.require_engagement_scope and not skip_scope_check:
            match = self._scope_matcher.evaluate(request.target_identifier, engagement.scope_rules)
            if not match.matched:
                decision = AuthorizationDecision(allowed=False, reason=match.reason)
                self._log_decision(request, decision)
                return decision

        if self._risk_policy.requires_human_approval(request.risk_level):
            pending = await self._pending.create(request)
            decision = AuthorizationDecision(
                allowed=False,
                reason=f"Risk level {request.risk_level.value} requires human approval.",
                requires_human_approval=True,
                approval_token=pending.token,
            )
            self._log_decision(request, decision)
            return decision

        decision = AuthorizationDecision(allowed=True, reason="Auto-approved: within scope and risk policy.")
        self._log_decision(request, decision)
        return decision

    async def record_human_approval(
        self, approval_token: str, approved_by: str, *, approved: bool
    ) -> AuthorizationDecision:
        entry = await self._pending.resolve(approval_token, approved=approved, approved_by=approved_by)
        if entry is None:
            return AuthorizationDecision(
                allowed=False, reason="Approval token not found or already resolved."
            )
        if not approved:
            return AuthorizationDecision(
                allowed=False, reason=f"Denied by human approver '{approved_by}'."
            )
        return AuthorizationDecision(
            allowed=True,
            reason=f"Approved by human approver '{approved_by}'.",
            approval_token=approval_token,
        )

    async def is_in_scope(self, engagement_id: str, target_identifier: str) -> bool:
        engagement = await self._engagements.get(engagement_id)
        if engagement is None:
            return False
        return self._scope_matcher.evaluate(target_identifier, engagement.scope_rules).matched

    def _log_decision(self, request: AuthorizationRequest, decision: AuthorizationDecision) -> None:
        logger.info(
            "authz.decision",
            engagement_id=request.engagement_id,
            plugin_name=request.plugin_name,
            tool_name=request.tool_name,
            risk_level=request.risk_level.value,
            requested_by=request.requested_by,
            target_identifier=request.target_identifier,
            allowed=decision.allowed,
            requires_human_approval=decision.requires_human_approval,
            reason=decision.reason,
        )