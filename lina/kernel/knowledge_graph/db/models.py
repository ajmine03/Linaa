"""SQLAlchemy ORM tables backing the Knowledge Graph."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from kernel.runtime.db.base import Base


class GraphNodeRecord(Base):
    __tablename__ = "kg_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_type: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(256))
    properties_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def properties(self) -> dict[str, Any]:
        return json.loads(self.properties_json) if self.properties_json else {}


class GraphEdgeRecord(Base):
    __tablename__ = "kg_edges"
    __table_args__ = (
        Index("ix_kg_edges_source_rel", "source_id", "relationship"),
        Index("ix_kg_edges_target_rel", "target_id", "relationship"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("kg_nodes.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("kg_nodes.id", ondelete="CASCADE"), index=True
    )
    relationship: Mapped[str] = mapped_column(String(64), index=True)
    properties_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def properties(self) -> dict[str, Any]:
        return json.loads(self.properties_json) if self.properties_json else {}