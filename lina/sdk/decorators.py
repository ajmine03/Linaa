"""Declarative decorators plugin authors use to register tools with metadata.

@tool wraps an async function, attaching a ToolSpec derived from the
decorator arguments and the function's type-hinted parameters (via a
lightweight Pydantic model built at decoration time), so plugin authors
never hand-write a parameters_schema by hand.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar, get_type_hints

from pydantic import BaseModel, ConfigDict, create_model

from kernel.entities.enums import ToolRiskLevel
from kernel.ports.tool_runtime import ToolResult, ToolSpec
from sdk.exceptions import ToolDeclarationError

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, ToolResult]])

_TOOL_SPEC_ATTR = "__lina_tool_spec__"
_AGENT_MARKER_ATTR = "__lina_agent__"


def _build_parameters_model(func: Callable[..., Any]) -> type[BaseModel]:
    """Introspect a handler's signature (excluding `parameters` dict-style
    handlers) to build a Pydantic model describing its expected inputs.

    Convention: tool handlers accept a single `parameters: dict[str, Any]`
    argument per the ToolHandler protocol; for schema generation, plugin
    authors instead define a companion Pydantic model and pass it via
    `params_model=` to @tool. This function is the fallback when none is
    given — it infers an empty/loose schema.
    """
    return create_model(f"{func.__name__.title()}Params", __config__=ConfigDict(extra="allow"))


def tool(
    *,
    name: str,
    plugin_name: str,
    description: str,
    risk_level: ToolRiskLevel,
    timeout_seconds: int = 120,
    requires_network: bool = False,
    tags: list[str] | None = None,
    params_model: type[BaseModel] | None = None,
) -> Callable[[F], F]:
    """Decorator registering static ToolSpec metadata on a handler function.

    Usage:
        @tool(
            name="port_scan",
            plugin_name="pentest",
            description="TCP port scan against an in-scope host.",
            risk_level=ToolRiskLevel.LOW,
            timeout_seconds=300,
        )
        async def port_scan(parameters: dict[str, Any]) -> ToolResult:
            ...
    """

    def decorator(func: F) -> F:
        if not inspect.iscoroutinefunction(func):
            raise ToolDeclarationError(
                f"Tool handler '{name}' must be an async function (async def)."
            )

        model = params_model or _build_parameters_model(func)
        schema = model.model_json_schema()

        spec = ToolSpec(
            name=name,
            plugin_name=plugin_name,
            description=description,
            risk_level=risk_level,
            parameters_schema=schema,
            timeout_seconds=timeout_seconds,
            requires_network=requires_network,
            tags=tags or [],
        )
        setattr(func, _TOOL_SPEC_ATTR, spec)
        return func

    return decorator


def get_tool_spec(func: Callable[..., Any]) -> ToolSpec | None:
    return getattr(func, _TOOL_SPEC_ATTR, None)


def agent(*, name: str, plugin_name: str) -> Callable[[type], type]:
    """Class decorator marking an AgentBase subclass for discovery by the
    Plugin Manager. Stores identity metadata used during plugin loading.
    """

    def decorator(cls: type) -> type:
        setattr(cls, _AGENT_MARKER_ATTR, {"name": name, "plugin_name": plugin_name})
        return cls

    return decorator


def get_agent_metadata(cls: type) -> dict[str, str] | None:
    return getattr(cls, _AGENT_MARKER_ATTR, None)