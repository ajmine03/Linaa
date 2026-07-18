"""Base class for stateful tool implementations that need more than a bare
async function (e.g. tools maintaining a persistent connection/client).

Most plugin tools should just use the @tool decorator on a plain async
function; ToolBase exists for cases needing setup/teardown lifecycle
(e.g. an authenticated API client reused across multiple tool calls).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from kernel.ports.tool_runtime import ToolResult


class ToolBase(ABC):
    """Lifecycle-aware tool implementation. Instances are callables satisfying
    the ToolHandler protocol via __call__, so they register identically to
    plain @tool-decorated functions: `registry.register(spec, tool_instance)`.
    """

    async def setup(self) -> None:
        """Optional one-time setup (e.g. open a client connection). No-op by default."""

    async def teardown(self) -> None:
        """Optional cleanup. No-op by default."""

    @abstractmethod
    async def run(self, parameters: dict[str, Any]) -> ToolResult:
        """Core tool logic — implement this instead of __call__ directly."""

    async def __call__(self, parameters: dict[str, Any]) -> ToolResult:
        return await self.run(parameters)