"""Memory Engine port — semantic + episodic memory backed by a vector store."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class MemoryRecord:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass(slots=True, frozen=True)
class MemoryQueryResult:
    record: MemoryRecord
    score: float


class MemoryEnginePort(ABC):
    """Stores and retrieves semantic memory (agent context, past findings,
    engagement history) scoped by collection (typically per-engagement or
    per-plugin) for retrieval-augmented agent reasoning.
    """

    @abstractmethod
    async def upsert(self, collection: str, records: list[MemoryRecord]) -> None: ...

    @abstractmethod
    async def query(
        self,
        collection: str,
        query_text: str,
        *,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[MemoryQueryResult]: ...

    @abstractmethod
    async def delete(self, collection: str, record_ids: list[str]) -> None: ...

    @abstractmethod
    async def delete_collection(self, collection: str) -> None: ...

    @abstractmethod
    async def get_by_id(self, collection: str, record_id: str) -> MemoryRecord | None: ...