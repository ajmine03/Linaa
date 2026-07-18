"""LINA Authorization Framework — the mandatory gate for every action-capable tool."""

from kernel.authz.framework import AuthorizationFramework, digest_parameters
from kernel.authz.pending_approvals import PendingApproval, PendingApprovalStore
from kernel.authz.policy import RiskPolicy
from kernel.authz.scope_matcher import ScopeMatcher, ScopeMatchResult

__all__ = [
    "AuthorizationFramework",
    "PendingApproval",
    "PendingApprovalStore",
    "RiskPolicy",
    "ScopeMatcher",
    "ScopeMatchResult",
    "digest_parameters",
]