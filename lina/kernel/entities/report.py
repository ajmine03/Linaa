"""Report entity: a generated deliverable summarizing engagement findings."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from kernel.entities.base import BaseEntity, utcnow
from kernel.entities.enums import ReportFormat


class Report(BaseEntity):
    """A generated report artifact, referencing findings from an engagement."""

    engagement_id: str
    title: str
    format: ReportFormat
    file_ref: str = Field(description="Path/key into the reports/ directory.")
    finding_ids: list[str] = Field(default_factory=list)
    generated_by: str = Field(description="Agent/plugin/user that generated this report.")
    generated_at: datetime = Field(default_factory=utcnow)
    executive_summary: str | None = None
    version: int = Field(default=1, ge=1)

    _entity_name = "Report"

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Report title must not be empty.")
        return v.strip()