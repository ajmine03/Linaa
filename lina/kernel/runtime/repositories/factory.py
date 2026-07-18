"""Factory functions producing concrete repository instances per entity type.

Centralizes the column_extractor mapping so callers never hand-roll a
SQLAlchemyRepository incorrectly.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from kernel.entities.agent_session import AgentSession, AgentStep
from kernel.entities.asset import Asset
from kernel.entities.credential import Credential
from kernel.entities.engagement import Engagement
from kernel.entities.event import AuditEntry
from kernel.entities.finding import Finding
from kernel.entities.report import Report
from kernel.entities.target import Target
from kernel.entities.tool_execution import ToolExecution
from kernel.runtime.db.models import (
    AgentSessionRecord,
    AgentStepRecord,
    AssetRecord,
    AuditEntryRecord,
    CredentialRecord,
    EngagementRecord,
    FindingRecord,
    ReportRecord,
    TargetRecord,
    ToolExecutionRecord,
)
from kernel.runtime.repositories.base_repository import SQLAlchemyRepository


def engagement_repository(session: AsyncSession) -> SQLAlchemyRepository[Engagement, EngagementRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=Engagement,
        record_cls=EngagementRecord,
        column_extractor=lambda e: {"status": e.status.value},
    )


def target_repository(session: AsyncSession) -> SQLAlchemyRepository[Target, TargetRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=Target,
        record_cls=TargetRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "target_type": e.target_type.value,
        },
    )


def finding_repository(session: AsyncSession) -> SQLAlchemyRepository[Finding, FindingRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=Finding,
        record_cls=FindingRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "severity": e.severity.value,
            "status": e.status.value,
        },
    )


def asset_repository(session: AsyncSession) -> SQLAlchemyRepository[Asset, AssetRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=Asset,
        record_cls=AssetRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "asset_type": e.asset_type.value,
        },
    )


def credential_repository(session: AsyncSession) -> SQLAlchemyRepository[Credential, CredentialRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=Credential,
        record_cls=CredentialRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "credential_type": e.credential_type.value,
        },
    )


def tool_execution_repository(
    session: AsyncSession,
) -> SQLAlchemyRepository[ToolExecution, ToolExecutionRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=ToolExecution,
        record_cls=ToolExecutionRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "status": e.status.value,
            "plugin_name": e.plugin_name,
        },
    )


def agent_session_repository(
    session: AsyncSession,
) -> SQLAlchemyRepository[AgentSession, AgentSessionRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=AgentSession,
        record_cls=AgentSessionRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "status": e.status.value,
            "plugin_name": e.plugin_name,
        },
    )


def agent_step_repository(session: AsyncSession) -> SQLAlchemyRepository[AgentStep, AgentStepRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=AgentStep,
        record_cls=AgentStepRecord,
        column_extractor=lambda e: {"agent_session_id": e.agent_session_id},
    )


def report_repository(session: AsyncSession) -> SQLAlchemyRepository[Report, ReportRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=Report,
        record_cls=ReportRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "format": e.format.value,
        },
    )


def audit_entry_repository(session: AsyncSession) -> SQLAlchemyRepository[AuditEntry, AuditEntryRecord]:
    return SQLAlchemyRepository(
        session,
        entity_cls=AuditEntry,
        record_cls=AuditEntryRecord,
        column_extractor=lambda e: {
            "engagement_id": e.engagement_id,
            "actor": e.actor,
            "action": e.action,
        },
    )


__all__ = [
    "agent_session_repository",
    "agent_step_repository",
    "asset_repository",
    "audit_entry_repository",
    "credential_repository",
    "engagement_repository",
    "finding_repository",
    "report_repository",
    "target_repository",
    "tool_execution_repository",
]