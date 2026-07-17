"""LINA kernel domain entities — framework-agnostic core models.

These are pure Pydantic v2 domain objects with no dependency on FastAPI,
SQLAlchemy, or any adapter. Persistence mapping happens in kernel/ports
implementations (repository adapters), never here.
"""

from kernel.entities.agent_session import AgentSession, AgentStep
from kernel.entities.asset import Asset
from kernel.entities.base import BaseEntity, EntityId, ValueObject, new_id, utcnow
from kernel.entities.credential import Credential
from kernel.entities.engagement import AuthorizationDocument, Engagement, ScopeRule
from kernel.entities.enums import (
    AgentSessionStatus,
    AssetType,
    CredentialType,
    EngagementStatus,
    EngagementType,
    EventSeverity,
    FindingSeverity,
    FindingStatus,
    ReportFormat,
    TargetType,
    ToolExecutionStatus,
    ToolRiskLevel,
)
from kernel.entities.event import AuditEntry, EventEnvelope
from kernel.entities.exceptions import (
    EntityError,
    EntityValidationError,
    InvalidStateTransitionError,
    ScopeViolationError,
)
from kernel.entities.finding import CVSSVector, Evidence, Finding
from kernel.entities.report import Report
from kernel.entities.target import Target
from kernel.entities.tool_execution import ToolExecution

__all__ = [
    "AgentSession",
    "AgentSessionStatus",
    "AgentStep",
    "Asset",
    "AssetType",
    "AuditEntry",
    "AuthorizationDocument",
    "BaseEntity",
    "CVSSVector",
    "Credential",
    "CredentialType",
    "Engagement",
    "EngagementStatus",
    "EngagementType",
    "EntityError",
    "EntityId",
    "EntityValidationError",
    "EventEnvelope",
    "EventSeverity",
    "Evidence",
    "Finding",
    "FindingSeverity",
    "FindingStatus",
    "InvalidStateTransitionError",
    "Report",
    "ReportFormat",
    "ScopeRule",
    "ScopeViolationError",
    "Target",
    "TargetType",
    "ToolExecution",
    "ToolExecutionStatus",
    "ToolRiskLevel",
    "ValueObject",
    "new_id",
    "utcnow",
]