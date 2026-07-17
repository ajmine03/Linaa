"""Credential entity: sensitive material discovered/harvested during engagements.

Handled distinctly from generic Assets because of elevated storage,
redaction, and access-control requirements enforced by the Authorization
Framework and Memory Engine.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from kernel.entities.base import BaseEntity
from kernel.entities.enums import CredentialType


class Credential(BaseEntity):
    """A discovered credential. `secret_ref` is a pointer, never the raw secret."""

    engagement_id: str
    target_id: str | None = None
    credential_type: CredentialType
    principal: str = Field(description="Username, key ID, or principal name.")
    secret_ref: str = Field(
        description="Opaque reference into the secret store/vault — never the "
        "plaintext secret itself. The domain layer never carries raw secrets."
    )
    source: str = Field(description="Where/how this credential was obtained.")
    validated: bool = Field(default=False)
    scope_note: str | None = Field(
        default=None, description="What this credential grants access to, if known."
    )

    _entity_name = "Credential"

    @field_validator("secret_ref")
    @classmethod
    def no_plaintext_leak_heuristic(cls, v: str) -> str:
        if len(v) > 4096:
            raise ValueError(
                "secret_ref is suspiciously large — raw secrets must not be "
                "stored on the Credential entity, only vault references."
            )
        return v