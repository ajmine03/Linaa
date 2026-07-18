"""Knowledge Graph port — relational/graph view over engagement entities.

Complements the Memory Engine's semantic search with explicit typed
relationships (host->service, service->finding, credential->grants->asset),
enabling multi-hop reasoning (e.g. attack-path queries) for agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class GraphNode:
    id: str
    node_type: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relationship: str
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphPort(ABC):
    @abstractmethod
    async def upsert_node(self, node: GraphNode) -> None: ...

    @abstractmethod
    async def upsert_edge(self, edge: GraphEdge) -> None: ...

    @abstractmethod
    async def get_node(self, node_id: str) -> GraphNode | None: ...

    @abstractmethod
    async def neighbors(
        self, node_id: str, *, relationship: str | None = None, direction: str = "out"
    ) -> list[tuple[GraphEdge, GraphNode]]:
        """direction: 'out' | 'in' | 'both'."""

    @abstractmethod
    async def find_paths(
        self, source_id: str, target_id: str, *, max_depth: int = 5
    ) -> list[list[GraphEdge]]:
        """Find candidate paths between two nodes (e.g. for attack-path analysis)."""

    @abstractmethod
    async def query_by_type(
        self, node_type: str, *, properties_filter: dict[str, Any] | None = None
    ) -> list[GraphNode]: ...

    @abstractmethod
    async def delete_node(self, node_id: str) -> bool: ...