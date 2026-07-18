"""LINA kernel ports — abstract hexagonal-architecture boundaries.

Every port here is an ABC depending only on kernel.entities and stdlib.
Concrete adapters (SQLAlchemy repos, Ollama model router, ChromaDB memory
engine, LangGraph workflow engine, etc.) live outside the kernel and are
wired together at composition-root time (kernel/runtime).
"""

from kernel.ports.authz import (
    AuthorizationDecision,
    AuthorizationPort,
    AuthorizationRequest,
)
from kernel.ports.event_bus import EventBusPort, EventHandler
from kernel.ports.exceptions import (
    AuthorizationDeniedError,
    ConflictError,
    EventBusError,
    KnowledgeGraphError,
    MCPError,
    ModelRouterError,
    NotFoundError,
    PortError,
    ToolRuntimeError,
    VectorStoreError,
)
from kernel.ports.knowledge_graph import GraphEdge, GraphNode, KnowledgeGraphPort
from kernel.ports.mcp import (
    MCPClientPort,
    MCPInvocationResult,
    MCPResource,
    MCPServerPort,
    MCPToolDescriptor,
)
from kernel.ports.memory_engine import MemoryEnginePort, MemoryQueryResult, MemoryRecord
from kernel.ports.model_router import (
    ChatMessage,
    ChatRole,
    EmbeddingResult,
    ModelCapability,
    ModelRequest,
    ModelResponse,
    ModelRouterPort,
)
from kernel.ports.prompt_registry import PromptRegistryPort, PromptTemplate
from kernel.ports.repository import EngagementScopedRepository, Repository
from kernel.ports.tool_runtime import (
    ToolHandler,
    ToolResult,
    ToolRuntimePort,
    ToolSpec,
)
from kernel.ports.unit_of_work import UnitOfWork
from kernel.ports.workflow_engine import (
    WorkflowDefinition,
    WorkflowEnginePort,
    WorkflowRunResult,
    WorkflowRunStatus,
)

__all__ = [
    "AuthorizationDecision",
    "AuthorizationDeniedError",
    "AuthorizationPort",
    "AuthorizationRequest",
    "ChatMessage",
    "ChatRole",
    "ConflictError",
    "EmbeddingResult",
    "EngagementScopedRepository",
    "EventBusError",
    "EventBusPort",
    "EventHandler",
    "GraphEdge",
    "GraphNode",
    "KnowledgeGraphError",
    "KnowledgeGraphPort",
    "MCPClientPort",
    "MCPError",
    "MCPInvocationResult",
    "MCPResource",
    "MCPServerPort",
    "MCPToolDescriptor",
    "MemoryEnginePort",
    "MemoryQueryResult",
    "MemoryRecord",
    "ModelCapability",
    "ModelRequest",
    "ModelResponse",
    "ModelRouterError",
    "ModelRouterPort",
    "NotFoundError",
    "PortError",
    "PromptRegistryPort",
    "PromptTemplate",
    "Repository",
    "ToolHandler",
    "ToolResult",
    "ToolRuntimeError",
    "ToolRuntimePort",
    "ToolSpec",
    "UnitOfWork",
    "VectorStoreError",
    "WorkflowDefinition",
    "WorkflowEnginePort",
    "WorkflowRunResult",
    "WorkflowRunStatus",
]