"""Breadth-first path search over the in-memory adjacency view of the graph.

Kept as a pure algorithm operating on plain (GraphEdge, GraphNode) tuples
so it has zero database dependency and is trivially unit-testable.
"""

from __future__ import annotations

from collections import deque

from kernel.ports.knowledge_graph import GraphEdge


class PathFinder:
    """BFS-based path enumeration between two nodes over a fetched edge set."""

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        adjacency: dict[str, list[GraphEdge]],
        *,
        max_depth: int = 5,
        max_paths: int = 10,
    ) -> list[list[GraphEdge]]:
        if source_id == target_id:
            return []

        found_paths: list[list[GraphEdge]] = []
        queue: deque[tuple[str, list[GraphEdge], set[str]]] = deque()
        queue.append((source_id, [], {source_id}))

        while queue and len(found_paths) < max_paths:
            current_id, path, visited = queue.popleft()

            if len(path) >= max_depth:
                continue

            for edge in adjacency.get(current_id, []):
                if edge.target_id in visited:
                    continue
                new_path = [*path, edge]
                if edge.target_id == target_id:
                    found_paths.append(new_path)
                    continue
                queue.append((edge.target_id, new_path, visited | {edge.target_id}))

        return found_paths