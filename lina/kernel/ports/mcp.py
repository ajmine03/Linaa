"""MCP (Model Context Protocol) port — LINA as both MCP client and MCP server.

As a client: LINA agents can consume external MCP tool servers.
As a server: LINA exposes its own tools/resources to external MCP clients
(e.g. Claude Desktop, other agent frameworks) under Authorization Framework
gating.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class MCPToolDescriptor:
    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str


@dataclass(slots=True, frozen=True)
class MCPResource:
    uri: str
    name: str
    mime_type: str | None = None
    description: str = ""


@dataclass(slots=True, frozen=True)
class MCPInvocationResult:
    content: list[dict[str, Any]]
    is_error: bool = False


class MCPClientPort(ABC):
    """LINA acting as a client to external MCP servers."""

    @abstractmethod
    async def connect(self, server_name: str, connection_uri: str) -> None: ...

    @abstractmethod
    async def disconnect(self, server_name: str) -> None: ...

    @abstractmethod
    async def list_tools(self, server_name: str | None = None) -> list[MCPToolDescriptor]: ...

    @abstractmethod
    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> MCPInvocationResult: ...

    @abstractmethod
    async def list_resources(self, server_name: str) -> list[MCPResource]: ...

    @abstractmethod
    async def read_resource(self, server_name: str, uri: str) -> str: ...


class MCPServerPort(ABC):
    """LINA exposing its own tool registry to external MCP clients."""

    @abstractmethod
    def expose_tool(self, descriptor: MCPToolDescriptor) -> None: ...

    @abstractmethod
    def expose_resource(self, resource: MCPResource) -> None: ...

    @abstractmethod
    async def start(self, *, host: str, port: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
    
    @abstractmethod
    def registered_tool_names(self) -> list[str]: ...