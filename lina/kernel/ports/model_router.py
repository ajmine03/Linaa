"""Model Router port — abstracts LLM backend selection and invocation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ModelCapability(StrEnum):
    CHAT = "chat"
    TOOL_USE = "tool_use"
    EMBEDDING = "embedding"
    VISION = "vision"
    REASONING = "reasoning"
    CODE = "code"


class ChatRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(slots=True, frozen=True)
class ChatMessage:
    role: ChatRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ModelRequest:
    """A normalized request the Model Router dispatches to a chosen backend model."""

    messages: list[ChatMessage]
    required_capabilities: list[ModelCapability] = field(
        default_factory=lambda: [ModelCapability.CHAT]
    )
    preferred_model: str | None = None
    temperature: float = 0.2
    max_tokens: int | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    stream: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ModelResponse:
    content: str
    model_used: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None


@dataclass(slots=True, frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    model_used: str
    dimensions: int


class ModelRouterPort(ABC):
    """Selects and invokes an appropriate local model (via Ollama or other
    backends) based on requested capabilities, load, and routing policy.
    """

    @abstractmethod
    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Non-streaming chat/completion call."""

    @abstractmethod
    def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Streaming chat/completion call, yielding content deltas."""

    @abstractmethod
    async def embed(
        self, texts: list[str], *, model: str | None = None
    ) -> EmbeddingResult:
        """Generate embeddings for one or more texts."""

    @abstractmethod
    async def health_check(self) -> dict[str, bool]:
        """Return {model_name: is_reachable} for all configured models."""

    @abstractmethod
    def resolve_model(
        self, capabilities: list[ModelCapability], preferred: str | None = None
    ) -> str:
        """Pure routing decision: which model name should serve this request."""