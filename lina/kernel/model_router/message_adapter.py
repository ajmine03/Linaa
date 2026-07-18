"""Converts LINA's transport-agnostic ChatMessage/ModelRequest into the
wire format expected by the `ollama` Python client, and normalizes
responses back into ModelResponse.
"""

from __future__ import annotations

from typing import Any

from kernel.ports.model_router import ChatMessage, ChatRole, ModelResponse


def to_ollama_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for msg in messages:
        entry: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
        if msg.tool_calls:
            entry["tool_calls"] = msg.tool_calls
        if msg.role == ChatRole.TOOL and msg.tool_call_id:
            entry["tool_call_id"] = msg.tool_call_id
        if msg.name:
            entry["name"] = msg.name
        result.append(entry)
    return result


def from_ollama_response(raw: dict[str, Any], *, model_used: str) -> ModelResponse:
    message = raw.get("message", {})
    content = message.get("content", "") or ""
    tool_calls = message.get("tool_calls", []) or []

    prompt_tokens = raw.get("prompt_eval_count")
    completion_tokens = raw.get("eval_count")

    done_reason = raw.get("done_reason")

    return ModelResponse(
        content=content,
        model_used=model_used,
        tool_calls=tool_calls,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        finish_reason=done_reason,
    )