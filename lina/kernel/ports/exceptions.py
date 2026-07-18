"""Exceptions shared across port contracts (raised by any adapter implementation)."""

from __future__ import annotations


class PortError(Exception):
    """Base exception for port-boundary failures."""


class NotFoundError(PortError):
    """Raised when a repository lookup finds no matching entity."""

    def __init__(self, entity_name: str, entity_id: str) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} not found: {entity_id}")


class ConflictError(PortError):
    """Raised on unique-constraint or optimistic-concurrency violations."""


class ModelRouterError(PortError):
    """Raised when the underlying LLM backend fails or is unreachable."""


class ToolRuntimeError(PortError):
    """Raised when a tool execution adapter fails outside normal exit-code failure."""


class AuthorizationDeniedError(PortError):
    """Raised when the Authorization Framework refuses an action."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Authorization denied: {reason}")


class EventBusError(PortError):
    """Raised on publish/subscribe failures within the Event Bus."""


class VectorStoreError(PortError):
    """Raised on Memory Engine / ChromaDB adapter failures."""


class KnowledgeGraphError(PortError):
    """Raised on Knowledge Graph adapter failures."""


class MCPError(PortError):
    """Raised on MCP client/server communication failures."""