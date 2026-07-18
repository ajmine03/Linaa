"""LINA Plugin SDK — the public API surface for plugin authors.

Plugin code should only ever import from `sdk` and `kernel.entities` /
`kernel.ports` (for types), never from kernel.runtime, kernel.authz, etc.
directly. All kernel service access flows through the injected PluginContext.
"""

from sdk.agent_base import AgentBase, AgentStepOutcome
from sdk.context import PluginContext, UnitOfWorkFactory
from sdk.decorators import agent, get_agent_metadata, get_tool_spec, tool
from sdk.exceptions import (
    AgentDeclarationError,
    PluginManifestError,
    SDKError,
    ToolDeclarationError,
)
from sdk.plugin_base import (
    AgentRegistration,
    PluginBase,
    PluginManifest,
    ToolRegistration,
)
from sdk.tool_base import ToolBase

__all__ = [
    "AgentBase",
    "AgentDeclarationError",
    "AgentRegistration",
    "AgentStepOutcome",
    "PluginBase",
    "PluginContext",
    "PluginManifest",
    "PluginManifestError",
    "SDKError",
    "ToolBase",
    "ToolDeclarationError",
    "ToolRegistration",
    "UnitOfWorkFactory",
    "agent",
    "get_agent_metadata",
    "get_tool_spec",
    "tool",
]