"""Workflow Engine port — orchestrates multi-step, multi-agent DAG/graph workflows.

The concrete adapter wraps LangGraph; this port keeps the kernel decoupled
from that specific library.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True, frozen=True)
class WorkflowDefinition:
    name: str
    plugin_name: str
    description: str
    entry_node: str
    version: int = 1


@dataclass(slots=True, frozen=True)
class WorkflowRunResult:
    run_id: str
    status: WorkflowRunStatus
    final_state: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


class WorkflowEnginePort(ABC):
    @abstractmethod
    def register_workflow(self, definition: WorkflowDefinition, graph: Any) -> None:
        """Register a compiled workflow graph (e.g. a LangGraph StateGraph)."""

    @abstractmethod
    async def start_run(
        self,
        workflow_name: str,
        *,
        engagement_id: str,
        initial_state: dict[str, Any],
        run_id: str | None = None,
    ) -> str:
        """Start a workflow run asynchronously. Returns the run_id."""

    @abstractmethod
    async def get_run_status(self, run_id: str) -> WorkflowRunStatus: ...

    @abstractmethod
    async def get_run_result(self, run_id: str) -> WorkflowRunResult: ...

    @abstractmethod
    async def cancel_run(self, run_id: str) -> bool: ...

    @abstractmethod
    async def resume_run(
        self, run_id: str, *, human_input: dict[str, Any]
    ) -> WorkflowRunResult:
        """Resume a workflow paused on a human-in-the-loop interrupt."""