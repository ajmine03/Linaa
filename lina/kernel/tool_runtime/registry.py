"""In-memory registry of ToolSpec declarations and their bound handlers."""

from __future__ import annotations

import structlog

from kernel.ports.tool_runtime import ToolHandler, ToolSpec

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """Holds every registered tool's static spec and its handler callable.

    Plugins register tools here during load (via Plugin Manager); the Tool
    Runtime consults this registry to resolve a tool_name into an
    executable handler + risk-level metadata before invoking Authorization.
    """

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        if spec.name in self._specs:
            logger.warning("tool_registry.overwriting_existing_tool", tool_name=spec.name)
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler
        logger.info(
            "tool_registry.registered",
            tool_name=spec.name,
            plugin_name=spec.plugin_name,
            risk_level=spec.risk_level.value,
        )

    def get_spec(self, tool_name: str) -> ToolSpec | None:
        return self._specs.get(tool_name)

    def get_handler(self, tool_name: str) -> ToolHandler | None:
        return self._handlers.get(tool_name)

    def list_specs(self, *, plugin_name: str | None = None) -> list[ToolSpec]:
        specs = list(self._specs.values())
        if plugin_name is not None:
            specs = [s for s in specs if s.plugin_name == plugin_name]
        return specs

    def unregister_plugin(self, plugin_name: str) -> int:
        to_remove = [name for name, spec in self._specs.items() if spec.plugin_name == plugin_name]
        for name in to_remove:
            del self._specs[name]
            del self._handlers[name]
        logger.info("tool_registry.unregistered_plugin", plugin_name=plugin_name, count=len(to_remove))
        return len(to_remove)