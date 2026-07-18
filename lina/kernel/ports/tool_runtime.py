"""Tool Runtime port — the contract for executing a single tool safely."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from kernel.entities.enums import ToolRiskLevel
from kernel.entities.tool_execution import ToolExecution


@dataclass(slots=True, frozen=True)
class ToolResult:
    """Normalized outcome of a tool invocation, independent of underlying transport."""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    structured_output: dict[str, Any] | None = None
    truncated: bool = False


@dataclass(slots=True, frozen=True)
class ToolSpec:
    """Static declaration of a tool's identity, risk, and parameter schema."""

    name: str
    plugin_name: str
    description: str
    risk_level: ToolRiskLevel
    parameters_schema: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 120
    requires_network: bool = False
    tags: list[str] = field(default_factory=list)


class ToolHandler(Protocol):
    """The callable contract every concrete tool implementation must satisfy."""

    async def __call__(self, parameters: dict[str, Any]) -> ToolResult: ...


class ToolRuntimePort(ABC):
    """Executes a ToolExecution against its registered handler with sandboxing,
    timeout enforcement, and output capture. Does NOT perform authorization —
    that's the AuthorizationFramework's job, invoked by the Tool Runtime
    component before this port is called.
    """

    @abstractmethod
    async def execute(
        self,
        spec: ToolSpec,
        execution: ToolExecution,
    ) -> ToolResult:
        """Run the tool. Must respect spec.timeout_seconds and never raise for
        normal tool failure (non-zero exit) — only for infrastructure errors
        (raises ToolRuntimeError in that case).
        """

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """Attempt to cancel an in-flight execution. Returns True if cancelled."""

    @abstractmethod
    def register_handler(self, tool_name: str, handler: ToolHandler) -> None:
        """Register the concrete implementation backing a declared ToolSpec."""

    @abstractmethod
    def register_tool(self, spec: ToolSpec, handler: ToolHandler) -> None:
        """Register a ToolSpec and its handler together in one call.

        Added for the Plugin Manager, which needs to register a plugin's
        declared tools without depending on a concrete adapter's internal
        registry. SubprocessToolRuntime already implements this.
        """

    @abstractmethod
    def get_spec(self, tool_name: str) -> ToolSpec | None:
        """Look up a registered tool's static spec."""

    @abstractmethod
    def list_specs(
        self,
        *,
        plugin_name: str | None = None,
    ) -> list[ToolSpec]:
        """List all registered tool specs, optionally filtered by plugin."""