"""PluginBase: the contract every LINA plugin package must implement.

Each plugin module (e.g. plugins/pentest/) exposes a `PLUGIN` module-level
instance of a PluginBase subclass, discovered by the Plugin Manager via
auto-discovery of plugins/<name>/plugin.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from kernel.ports.tool_runtime import ToolHandler, ToolSpec
from sdk.agent_base import AgentBase


@dataclass(slots=True, frozen=True)
class PluginManifest:
    """Static plugin identity and metadata, independent of runtime wiring."""

    name: str
    version: str
    description: str
    author: str = "LINA Project"
    requires_network: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ToolRegistration:
    spec: ToolSpec
    handler: ToolHandler


@dataclass(slots=True, frozen=True)
class AgentRegistration:
    name: str
    agent_cls: type[AgentBase]


class PluginBase(ABC):
    """Every plugin implements this to declare its manifest, tools, and agents.

    The Plugin Manager calls `load()` once at startup (or on-demand) to
    obtain everything needed to register the plugin into the kernel's
    Tool Registry, Prompt Registry, and Agent Runtime.
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest: ...

    @abstractmethod
    def get_tools(self) -> list[ToolRegistration]:
        """Return every tool this plugin exposes, spec + handler bound together."""

    def get_agents(self) -> list[AgentRegistration]:
        """Return every agent class this plugin exposes. Optional — plugins
        with no autonomous agent (pure tool libraries) may leave this empty.
        """
        return []

    async def on_load(self) -> None:
        """Optional hook invoked once when the Plugin Manager loads this plugin
        (e.g. to validate external tool binaries are present on PATH).
        """

    async def on_unload(self) -> None:
        """Optional hook invoked when the plugin is unloaded/disabled."""