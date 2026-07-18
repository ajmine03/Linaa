"""SDK-level exceptions surfaced to plugin authors."""

from __future__ import annotations


class SDKError(Exception):
    """Base exception for all plugin-development-facing errors."""


class PluginManifestError(SDKError):
    """Raised when a plugin's manifest/declaration is malformed."""


class ToolDeclarationError(SDKError):
    """Raised when a @tool-decorated function has an invalid signature/schema."""


class AgentDeclarationError(SDKError):
    """Raised when an agent class fails to satisfy the AgentBase contract."""