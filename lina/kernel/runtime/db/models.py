"""Concrete SQLAlchemy ORM tables — one per domain entity type."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from kernel.runtime.db.base import Base, EngagementScopedMixin, EntityRecordMixin


class EngagementRecord(Base, EntityRecordMixin):
    __tablename__ = "engagements"
    status: Mapped[str] = mapped_column(String(32), index=True)


class TargetRecord(Base, EngagementScopedMixin):
    __tablename__ = "targets"
    target_type: Mapped[str] = mapped_column(String(32), index=True)


class FindingRecord(Base, EngagementScopedMixin):
    __tablename__ = "findings"
    severity: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)


class AssetRecord(Base, EngagementScopedMixin):
    __tablename__ = "assets"
    asset_type: Mapped[str] = mapped_column(String(32), index=True)


class CredentialRecord(Base, EngagementScopedMixin):
    __tablename__ = "credentials"
    credential_type: Mapped[str] = mapped_column(String(32), index=True)


class ToolExecutionRecord(Base, EngagementScopedMixin):
    __tablename__ = "tool_executions"
    status: Mapped[str] = mapped_column(String(32), index=True)
    plugin_name: Mapped[str] = mapped_column(String(64), index=True)


class AgentSessionRecord(Base, EngagementScopedMixin):
    __tablename__ = "agent_sessions"
    status: Mapped[str] = mapped_column(String(32), index=True)
    plugin_name: Mapped[str] = mapped_column(String(64), index=True)


class AgentStepRecord(Base, EntityRecordMixin):
    __tablename__ = "agent_steps"
    agent_session_id: Mapped[str] = mapped_column(String(36), index=True)


class ReportRecord(Base, EngagementScopedMixin):
    __tablename__ = "reports"
    format: Mapped[str] = mapped_column(String(16), index=True)


class AuditEntryRecord(Base, EntityRecordMixin):
    __tablename__ = "audit_entries"
    engagement_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    actor: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)