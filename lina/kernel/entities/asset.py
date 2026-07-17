"""Asset entity: an inventory item discovered/tracked during an engagement.

Distinct from Target: a Target is something explicitly in-scope to attack;
an Asset is anything discovered along the way (open port, running service,
cloud bucket, AD group, container image layer, etc.) that enriches the
Knowledge Graph.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from kernel.entities.base import BaseEntity
from kernel.entities.enums import AssetType


class Asset(BaseEntity):
    """A discovered inventory item linked to a Target within an Engagement."""


    engagement_id: str
    target_id: str | None = None
    asset_type: AssetType
    name: str
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form structured attributes, e.g. {'port': 443, 'service': 'https'}.",
    )
    discovered_by: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    related_finding_ids: list[str] = Field(default_factory=list)

    _entity_name = "Asset"

    def link_finding(self, finding_id: str) -> None:
        if finding_id not in self.related_finding_ids:
            self.related_finding_ids.append(finding_id)
            self.touch()