"""Concrete KnowledgeGraphPort implementation backed by SQLite via SQLAlchemy.

Shares the same database as the rest of LINA's kernel persistence (single
SQLite file, per the finalized architecture) but uses dedicated node/edge
tables rather than the generic entity-JSON pattern, since graph traversal
benefits from real relational indexes on source_id/target_id/relationship.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from kernel.knowledge_graph.db.models import GraphEdgeRecord, GraphNodeRecord
from kernel.knowledge_graph.path_finder import PathFinder
from kernel.ports.exceptions import KnowledgeGraphError
from kernel.ports.knowledge_graph import GraphEdge, GraphNode, KnowledgeGraphPort

logger = structlog.get_logger(__name__)


def _node_record_to_entity(record: GraphNodeRecord) -> GraphNode:
    return GraphNode(
        id=record.id,
        node_type=record.node_type,
        label=record.label,
        properties=record.properties(),
    )


def _edge_record_to_entity(record: GraphEdgeRecord) -> GraphEdge:
    return GraphEdge(
        source_id=record.source_id,
        target_id=record.target_id,
        relationship=record.relationship,
        properties=record.properties(),
    )


class SQLiteKnowledgeGraph(KnowledgeGraphPort):
    """One instance is bound to a single AsyncSession (consistent with the
    Unit-of-Work pattern used elsewhere in the kernel). Callers obtain a
    fresh instance per transaction scope.
    """

    def __init__(self, session: AsyncSession, *, path_finder: PathFinder | None = None) -> None:
        self._session = session
        self._path_finder = path_finder or PathFinder()

    async def upsert_node(self, node: GraphNode) -> None:
        try:
            existing = await self._session.get(GraphNodeRecord, node.id)
            props_json = json.dumps(node.properties, separators=(",", ":"), default=str)
            if existing is None:
                record = GraphNodeRecord(
                    id=node.id,
                    node_type=node.node_type,
                    label=node.label,
                    properties_json=props_json,
                    created_at=datetime.now(UTC),
                )
                self._session.add(record)
            else:
                existing.node_type = node.node_type
                existing.label = node.label
                existing.properties_json = props_json
            await self._session.flush()
        except Exception as exc:  # noqa: BLE001
            raise KnowledgeGraphError(f"upsert_node failed for {node.id}: {exc}") from exc

    async def upsert_edge(self, edge: GraphEdge) -> None:
        try:
            stmt = select(GraphEdgeRecord).where(
                GraphEdgeRecord.source_id == edge.source_id,
                GraphEdgeRecord.target_id == edge.target_id,
                GraphEdgeRecord.relationship == edge.relationship,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()
            props_json = json.dumps(edge.properties, separators=(",", ":"), default=str)

            if existing is None:
                record = GraphEdgeRecord(
                    id=str(uuid.uuid4()),
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relationship=edge.relationship,
                    properties_json=props_json,
                    created_at=datetime.now(UTC),
                )
                self._session.add(record)
            else:
                existing.properties_json = props_json
            await self._session.flush()
        except Exception as exc:  # noqa: BLE001
            raise KnowledgeGraphError(
                f"upsert_edge failed for {edge.source_id}->{edge.target_id}: {exc}"
            ) from exc

    async def get_node(self, node_id: str) -> GraphNode | None:
        record = await self._session.get(GraphNodeRecord, node_id)
        return _node_record_to_entity(record) if record else None

    async def neighbors(
        self, node_id: str, *, relationship: str | None = None, direction: str = "out"
    ) -> list[tuple[GraphEdge, GraphNode]]:
        if direction not in ("out", "in", "both"):
            raise KnowledgeGraphError(f"Invalid direction '{direction}'; must be out/in/both.")

        results: list[tuple[GraphEdge, GraphNode]] = []

        if direction in ("out", "both"):
            results.extend(await self._fetch_direction(node_id, relationship, outbound=True))
        if direction in ("in", "both"):
            results.extend(await self._fetch_direction(node_id, relationship, outbound=False))

        return results

    async def _fetch_direction(
        self, node_id: str, relationship: str | None, *, outbound: bool
    ) -> list[tuple[GraphEdge, GraphNode]]:
        anchor_col = GraphEdgeRecord.source_id if outbound else GraphEdgeRecord.target_id
        other_col = GraphEdgeRecord.target_id if outbound else GraphEdgeRecord.source_id

        stmt = select(GraphEdgeRecord).where(anchor_col == node_id)
        if relationship is not None:
            stmt = stmt.where(GraphEdgeRecord.relationship == relationship)

        result = await self._session.execute(stmt)
        edge_records = result.scalars().all()

        pairs: list[tuple[GraphEdge, GraphNode]] = []
        for edge_record in edge_records:
            other_id = getattr(edge_record, other_col.key)
            node_record = await self._session.get(GraphNodeRecord, other_id)
            if node_record is None:
                continue
            pairs.append((_edge_record_to_entity(edge_record), _node_record_to_entity(node_record)))
        return pairs

    async def find_paths(
        self, source_id: str, target_id: str, *, max_depth: int = 5
    ) -> list[list[GraphEdge]]:
        adjacency = await self._build_adjacency(max_hops=max_depth)
        return self._path_finder.find_paths(source_id, target_id, adjacency, max_depth=max_depth)

    async def _build_adjacency(self, *, max_hops: int) -> dict[str, list[GraphEdge]]:
        """Loads the full edge set once for BFS traversal.

        Acceptable at LINA's target scale (single-operator, single-engagement
        graphs realistically in the thousands of nodes/edges, not millions).
        """
        result = await self._session.execute(select(GraphEdgeRecord))
        records = result.scalars().all()
        adjacency: dict[str, list[GraphEdge]] = {}
        for record in records:
            edge = _edge_record_to_entity(record)
            adjacency.setdefault(edge.source_id, []).append(edge)
        return adjacency

    async def query_by_type(
        self, node_type: str, *, properties_filter: dict[str, object] | None = None
    ) -> list[GraphNode]:
        stmt = select(GraphNodeRecord).where(GraphNodeRecord.node_type == node_type)
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        nodes = [_node_record_to_entity(r) for r in records]

        if properties_filter:
            nodes = [
                n
                for n in nodes
                if all(n.properties.get(k) == v for k, v in properties_filter.items())
            ]
        return nodes

    async def delete_node(self, node_id: str) -> bool:
        record = await self._session.get(GraphNodeRecord, node_id)
        if record is None:
            return False
        await self._session.execute(
            delete(GraphEdgeRecord).where(
                (GraphEdgeRecord.source_id == node_id) | (GraphEdgeRecord.target_id == node_id)
            )
        )
        await self._session.delete(record)
        await self._session.flush()
        return True