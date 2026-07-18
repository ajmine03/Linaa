"""Pure routing-decision logic: maps requested capabilities to a model name.

Kept separate from the Ollama adapter so routing rules can be unit-tested
without a live Ollama instance and can later be swapped for a smarter
policy (load-based, latency-based) without touching the transport code.
"""

from __future__ import annotations

import structlog

from kernel.config.schema import OllamaConfig
from kernel.ports.model_router import ModelCapability

logger = structlog.get_logger(__name__)


class RoutingPolicy:
    """Resolves which configured model should serve a given capability set.

    Resolution order:
      1. If `preferred` is explicitly given, always honor it (caller knows best).
      2. If REASONING or CODE is required, use the reasoning model.
      3. If EMBEDDING is required (and nothing else), use the embedding model.
      4. Otherwise, use the default chat model.
    """

    def __init__(self, config: OllamaConfig) -> None:
        self._config = config

    def resolve(
        self, capabilities: list[ModelCapability], preferred: str | None = None
    ) -> str:
        if preferred:
            return preferred

        capset = set(capabilities)

        if ModelCapability.EMBEDDING in capset and len(capset) == 1:
            return self._config.embedding_model

        if ModelCapability.REASONING in capset or ModelCapability.CODE in capset:
            return self._config.reasoning_model

        return self._config.default_model

    def all_configured_models(self) -> list[str]:
        return list(
            {
                self._config.default_model,
                self._config.reasoning_model,
                self._config.embedding_model,
            }
        )