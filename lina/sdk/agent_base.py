"""Base class for plugin agents — LLM-driven, tool-using autonomous components.

Concrete agent implementations (per-plugin: PentestReconAgent, OSINTAgent,
CodingAgent, etc.) subclass this and implement `step()`, which the Agent
Runtime (kernel/agent_runtime) drives in a loop, persisting AgentStep
records and publishing lifecycle events after each step.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from kernel.entities.agent_session import AgentSession
from sdk.context import PluginContext


@dataclass(slots=True, frozen=True)
class AgentStepOutcome:
    """What an agent's single step produced — the Agent Runtime persists this
    as an AgentStep and decides whether to continue looping.
    """

    thought: str | None
    action: str | None
    action_input: dict[str, object]
    observation: str | None
    is_final: bool = False
    final_answer: str | None = None


class AgentBase(ABC):
    """Contract every plugin agent must implement.

    Subclasses are typically decorated with @sdk.decorators.agent(name=...,
    plugin_name=...) so the Plugin Manager can discover and register them.
    """

    def __init__(self, context: PluginContext, session: AgentSession) -> None:
        self.context = context
        self.session = session

    @abstractmethod
    async def step(self) -> AgentStepOutcome:
        """Execute one reasoning/action step and return its outcome.

        Called repeatedly by the Agent Runtime until `is_final` is True,
        `session.steps_remaining` reaches 0, or the runtime is cancelled.
        Implementations should read prior steps from `self.session` /
        the Memory Engine (via context) to maintain continuity, since no
        implicit conversation state is held between calls.
        """

    async def on_start(self) -> None:
        """Optional hook invoked once before the first step()."""

    async def on_complete(self, outcome: AgentStepOutcome) -> None:
        """Optional hook invoked once after the final step()."""

    async def on_error(self, error: Exception) -> None:
        """Optional hook invoked if step() raises. Default: re-raise."""
        raise error