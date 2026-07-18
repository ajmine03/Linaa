"""PluginContext: the single object plugins use to reach kernel services.

This is the SDK's dependency-injection surface — plugin code never imports
kernel.runtime, kernel.authz, etc. directly. Instead every tool handler and
agent receives a PluginContext giving scoped access to exactly what's
needed, keeping the hexagon boundary intact from the plugin side too.
"""

from __future__ import annotations

from dataclasses import dataclass

from kernel.ports.authz import AuthorizationPort
from kernel.ports.event_bus import EventBusPort
from kernel.ports.knowledge_graph import KnowledgeGraphPort
from kernel.ports.memory_engine import MemoryEnginePort
from kernel.ports.model_router import ModelRouterPort
from kernel.ports.prompt_registry import PromptRegistryPort
from kernel.ports.tool_runtime import ToolRuntimePort
from kernel.ports.unit_of_work import UnitOfWork


@dataclass(slots=True, frozen=True)
class PluginContext:
    """Scoped handle to kernel services, injected into every plugin component.

    `engagement_id` is bound at agent-session/tool-execution creation time
    and is always present — plugins never operate outside an engagement.
    """

    engagement_id: str
    plugin_name: str
    event_bus: EventBusPort
    model_router: ModelRouterPort
    memory_engine: MemoryEnginePort
    authz: AuthorizationPort
    tool_runtime: ToolRuntimePort
    prompt_registry: PromptRegistryPort
    knowledge_graph: KnowledgeGraphPort
    unit_of_work_factory: "UnitOfWorkFactory"

    def new_unit_of_work(self) -> UnitOfWork:
        return self.unit_of_work_factory()


from collections.abc import Callable  # noqa: E402

UnitOfWorkFactory = Callable[[], UnitOfWork]