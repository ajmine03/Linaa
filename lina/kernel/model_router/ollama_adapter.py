"""Concrete ModelRouterPort implementation backed by a local Ollama daemon."""

from __future__ import annotations

from collections.abc import AsyncIterator

import ollama
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from kernel.config.schema import OllamaConfig
from kernel.model_router.message_adapter import from_ollama_response, to_ollama_messages
from kernel.model_router.routing_policy import RoutingPolicy
from kernel.ports.exceptions import ModelRouterError
from kernel.ports.model_router import (
    EmbeddingResult,
    ModelCapability,
    ModelRequest,
    ModelResponse,
    ModelRouterPort,
)

logger = structlog.get_logger(__name__)

_RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError, OSError)


class OllamaModelRouter(ModelRouterPort):
    """Routes ModelRequests to the appropriate local Ollama model.

    Uses the async `ollama.AsyncClient` under the hood. Retries transient
    connection failures with exponential backoff (bounded by
    config.max_retries) — Ollama running locally can occasionally be slow
    to load a model into memory on first call.
    """

    def __init__(self, config: OllamaConfig, *, policy: RoutingPolicy | None = None) -> None:
        self._config = config
        self._policy = policy or RoutingPolicy(config)
        self._client = ollama.AsyncClient(
            host=config.base_url, timeout=config.request_timeout_seconds
        )

    def resolve_model(
        self, capabilities: list[ModelCapability], preferred: str | None = None
    ) -> str:
        return self._policy.resolve(capabilities, preferred)

    async def complete(self, request: ModelRequest) -> ModelResponse:
        model_name = self.resolve_model(request.required_capabilities, request.preferred_model)
        messages = to_ollama_messages(request.messages)

        logger.debug(
            "model_router.complete_starting",
            model=model_name,
            message_count=len(messages),
            has_tools=bool(request.tools),
        )

        try:
            response = await self._call_with_retry(
                model=model_name,
                messages=messages,
                tools=request.tools or None,
                options={
                    "temperature": request.temperature,
                    **({"num_predict": request.max_tokens} if request.max_tokens else {}),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("model_router.complete_failed", model=model_name)
            raise ModelRouterError(f"Ollama completion failed for model '{model_name}': {exc}") from exc

        result = from_ollama_response(response, model_used=model_name)
        logger.debug(
            "model_router.complete_finished",
            model=model_name,
            completion_tokens=result.completion_tokens,
            finish_reason=result.finish_reason,
        )
        return result

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_with_retry(self, **kwargs: object) -> dict[str, object]:
        result = await self._client.chat(
            keep_alive=self._config.keep_alive,
            **kwargs,  # type: ignore[arg-type]
        )
        return dict(result)

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Async-generator implementation.

        NOTE: this MUST be declared `async def` (not plain `def`) because the
        body contains both `await` and `yield`. A plain `def` here would be a
        SyntaxError ('await' outside async function) — the port's abstract
        signature is declared as `def ... -> AsyncIterator[str]` only because
        it's a stub method (body is `...`), which never executes and so is
        exempt from this constraint; concrete implementations must be async.
        """
        model_name = self.resolve_model(request.required_capabilities, request.preferred_model)
        messages = to_ollama_messages(request.messages)

        logger.debug("model_router.stream_starting", model=model_name)

        try:
            stream = await self._client.chat(
                model=model_name,
                messages=messages,
                stream=True,
                keep_alive=self._config.keep_alive,
                options={"temperature": request.temperature},
            )
            async for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
        except Exception as exc:  # noqa: BLE001
            logger.exception("model_router.stream_failed", model=model_name)
            raise ModelRouterError(f"Ollama streaming failed for model '{model_name}': {exc}") from exc

    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbeddingResult:
        model_name = model or self._config.embedding_model

        if not texts:
            raise ModelRouterError("Cannot embed an empty list of texts.")

        try:
            response = await self._embed_with_retry(model=model_name, input=texts)
        except Exception as exc:  # noqa: BLE001
            logger.exception("model_router.embed_failed", model=model_name)
            raise ModelRouterError(f"Ollama embedding failed for model '{model_name}': {exc}") from exc

        vectors = response.get("embeddings", [])
        dimensions = len(vectors[0]) if vectors else 0

        return EmbeddingResult(vectors=vectors, model_used=model_name, dimensions=dimensions)

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _embed_with_retry(self, **kwargs: object) -> dict[str, object]:
        result = await self._client.embed(**kwargs)  # type: ignore[arg-type]
        return dict(result)

    async def health_check(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for model_name in self._policy.all_configured_models():
            try:
                await self._client.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    options={"num_predict": 1},
                    keep_alive="1s",
                )
                results[model_name] = True
            except Exception:  # noqa: BLE001
                logger.warning("model_router.health_check_failed", model=model_name)
                results[model_name] = False
        return results