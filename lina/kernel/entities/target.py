"""Target entity: a concrete asset-in-scope under an Engagement."""

from __future__ import annotations

from pydantic import Field, field_validator

from kernel.entities.base import BaseEntity
from kernel.entities.enums import TargetType


class Target(BaseEntity):
    """A single addressable target under an engagement's scope.

    Targets are the atomic units that tools/agents act upon. Every Target
    must resolve to at least one ScopeRule on its parent Engagement before
    the Authorization Framework will permit action-capable tool execution.
    """

    engagement_id: str
    target_type: TargetType
    identifier: str = Field(
        description="The addressable value: IP, CIDR, domain, URL, account ID, etc."
    )
    display_name: str | None = None
    description: str | None = None
    in_scope: bool = Field(
        default=True,
        description="Explicit flag; can be set False to fence off a target "
        "even if it structurally matches an engagement scope rule.",
    )
    discovered_via: str | None = Field(
        default=None, description="Tool/agent/plugin that discovered this target, if any."
    )
    parent_target_id: str | None = Field(
        default=None, description="For hierarchical targets, e.g. a host under an IP range."
    )
    tags: list[str] = Field(default_factory=list)

    _entity_name = "Target"

    @field_validator("identifier")
    @classmethod
    def identifier_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Target identifier must not be empty.")
        return v.strip()

    def effective_scope(self) -> bool:
        return self.in_scope