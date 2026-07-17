"""Finding entity: a security-relevant observation, vulnerability, or fact."""

from __future__ import annotations

from pydantic import Field, field_validator

from kernel.entities.base import BaseEntity, ValueObject
from kernel.entities.enums import FindingSeverity, FindingStatus


class Evidence(ValueObject):
    """A single piece of supporting evidence attached to a Finding."""

    description: str
    artifact_path: str | None = Field(
        default=None, description="Path within the reports/evidence store, if a file."
    )
    raw_excerpt: str | None = Field(
        default=None, description="Short raw text excerpt (e.g. HTTP response snippet)."
    )
    source_tool: str | None = None


class CVSSVector(ValueObject):
    """Optional CVSS scoring attached to a finding."""

    version: str = Field(default="3.1")
    vector_string: str
    base_score: float = Field(ge=0.0, le=10.0)


class Finding(BaseEntity):
    """A discrete security finding, tied to an Engagement and (optionally) a Target."""

    engagement_id: str
    target_id: str | None = None
    title: str
    description: str
    severity: FindingSeverity
    status: FindingStatus = Field(default=FindingStatus.OPEN)
    cwe_ids: list[str] = Field(default_factory=list)
    cve_ids: list[str] = Field(default_factory=list)
    cvss: CVSSVector | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    remediation: str | None = None
    discovered_by: str = Field(
        description="Plugin/agent/tool identifier that produced this finding."
    )
    affected_component: str | None = None
    references: list[str] = Field(default_factory=list)
    duplicate_of: str | None = None

    _entity_name = "Finding"

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Finding title must not be empty.")
        return v.strip()

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)
        self.touch()

    def mark_status(self, status: FindingStatus, *, duplicate_of: str | None = None) -> None:
        self.status = status
        if status == FindingStatus.DUPLICATE:
            self.duplicate_of = duplicate_of
        self.touch()

    @property
    def risk_score(self) -> float:
        """Simple numeric risk score derived from severity, for sorting/reporting."""
        weights = {
            FindingSeverity.INFO: 0.0,
            FindingSeverity.LOW: 2.5,
            FindingSeverity.MEDIUM: 5.0,
            FindingSeverity.HIGH: 7.5,
            FindingSeverity.CRITICAL: 10.0,
        }
        base = self.cvss.base_score if self.cvss else weights[self.severity]
        return base