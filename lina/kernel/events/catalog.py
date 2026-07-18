"""Canonical event-type catalog for the LINA Event Bus.

Centralizing event names as constants prevents typo-drift between publishers
and subscribers scattered across plugins. Dotted namespace convention:
    <domain>.<entity>.<action>
"""

from __future__ import annotations

from typing import Final


class EventTypes:
    """Dotted event-type name constants. Use these instead of raw strings."""

    # Engagement lifecycle
    ENGAGEMENT_CREATED: Final[str] = "engagement.created"
    ENGAGEMENT_ACTIVATED: Final[str] = "engagement.activated"
    ENGAGEMENT_PAUSED: Final[str] = "engagement.paused"
    ENGAGEMENT_COMPLETED: Final[str] = "engagement.completed"
    ENGAGEMENT_CANCELLED: Final[str] = "engagement.cancelled"

    # Target lifecycle
    TARGET_ADDED: Final[str] = "target.added"
    TARGET_DISCOVERED: Final[str] = "target.discovered"

    # Findings
    FINDING_CREATED: Final[str] = "finding.created"
    FINDING_UPDATED: Final[str] = "finding.updated"
    FINDING_STATUS_CHANGED: Final[str] = "finding.status_changed"

    # Assets
    ASSET_DISCOVERED: Final[str] = "asset.discovered"
    ASSET_UPDATED: Final[str] = "asset.updated"

    # Credentials
    CREDENTIAL_DISCOVERED: Final[str] = "credential.discovered"
    CREDENTIAL_VALIDATED: Final[str] = "credential.validated"

    # Tool execution
    TOOL_EXECUTION_REQUESTED: Final[str] = "tool_execution.requested"
    TOOL_EXECUTION_APPROVED: Final[str] = "tool_execution.approved"
    TOOL_EXECUTION_DENIED: Final[str] = "tool_execution.denied"
    TOOL_EXECUTION_STARTED: Final[str] = "tool_execution.started"
    TOOL_EXECUTION_COMPLETED: Final[str] = "tool_execution.completed"
    TOOL_EXECUTION_FAILED: Final[str] = "tool_execution.failed"

    # Agent sessions
    AGENT_SESSION_STARTED: Final[str] = "agent_session.started"
    AGENT_SESSION_STEP: Final[str] = "agent_session.step"
    AGENT_SESSION_WAITING_APPROVAL: Final[str] = "agent_session.waiting_approval"
    AGENT_SESSION_COMPLETED: Final[str] = "agent_session.completed"
    AGENT_SESSION_FAILED: Final[str] = "agent_session.failed"

    # Workflow engine
    WORKFLOW_RUN_STARTED: Final[str] = "workflow.run_started"
    WORKFLOW_RUN_COMPLETED: Final[str] = "workflow.run_completed"
    WORKFLOW_RUN_FAILED: Final[str] = "workflow.run_failed"
    WORKFLOW_RUN_INTERRUPTED: Final[str] = "workflow.run_interrupted"

    # Authorization
    AUTHZ_DECISION_MADE: Final[str] = "authz.decision_made"
    AUTHZ_HUMAN_APPROVAL_REQUESTED: Final[str] = "authz.human_approval_requested"
    AUTHZ_HUMAN_APPROVAL_RESOLVED: Final[str] = "authz.human_approval_resolved"

    # Plugin lifecycle
    PLUGIN_LOADED: Final[str] = "plugin.loaded"
    PLUGIN_LOAD_FAILED: Final[str] = "plugin.load_failed"
    PLUGIN_UNLOADED: Final[str] = "plugin.unloaded"

    # Reports
    REPORT_GENERATED: Final[str] = "report.generated"

    # System / kernel
    SYSTEM_STARTED: Final[str] = "system.started"
    SYSTEM_SHUTDOWN: Final[str] = "system.shutdown"

    ALL_WILDCARD: Final[str] = "*"