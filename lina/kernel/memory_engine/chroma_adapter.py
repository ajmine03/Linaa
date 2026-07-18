"""Concrete MemoryEnginePort implementation backed by ChromaDB (persistent, local)."""

from __future__ import annotations

from typing import Any, cast

import chromadb
import structlog
from chromadb.api.types import Embeddings, Metadatas
from chromadb.config import Settings as ChromaSettings

from kernel.config.schema import ChromaDBConfig
from kernel.memory_engine.collection_naming import build_collection_name
from kernel.ports.exceptions import VectorStoreError
from kernel.ports.memory_engine import MemoryEnginePort, MemoryQueryResult, MemoryRecord
from kernel.ports.model_router import ModelRouterPort

logger = structlog.get_logger(__name__)


class ChromaMemoryEngine(MemoryEnginePort):
    """Local, persistent vector store for semantic agent memory.

    Embedding generation is delegated to the injected ModelRouterPort
    (Ollama's embedding model) rather than ChromaDB's built-in embedding
    functions, keeping a single consistent embedding pipeline across the
    Memory Engine and Knowledge Graph.
    """

    def __init__(self, config: ChromaDBConfig, model_router: ModelRouterPort) -> None:
        self._config = config
        self._model_router = model_router
        self._client = chromadb.PersistentClient(
            path=str(config.persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection_cache: dict[str, chromadb.Collection] = {}

    def _get_collection(self, collection: str) -> chromadb.Collection:
        name = build_collection_name(self._config.collection_prefix, collection)
        if name not in self._collection_cache:
            self._collection_cache[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": self._config.distance_metric},
            )
        return self._collection_cache[name]

    async def upsert(self, collection: str, records: list[MemoryRecord]) -> None:
        if not records:
            return

        chroma_collection = self._get_collection(collection)

        texts_needing_embedding = [r.text for r in records if r.embedding is None]
        embeddings_by_text: dict[str, list[float]] = {}

        if texts_needing_embedding:
            try:
                result = await self._model_router.embed(texts_needing_embedding)
            except Exception as exc:  # noqa: BLE001
                raise VectorStoreError(
                    f"Failed to embed records for upsert: {exc}"
                ) from exc

            for text, vector in zip(
                texts_needing_embedding,
                result.vectors,
                strict=True,
            ):
                embeddings_by_text[text] = vector

        ids = [r.id for r in records]
        documents = [r.text for r in records]

        metadatas = cast(
            Metadatas,
            [self._sanitize_metadata(r.metadata) for r in records],
        )

        embeddings = cast(
            Embeddings,
            [
                r.embedding
                if r.embedding is not None
                else embeddings_by_text[r.text]
                for r in records
            ],
        )

        try:
            chroma_collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"ChromaDB upsert failed for collection '{collection}': {exc}"
            ) from exc

        logger.debug(
            "memory_engine.upserted",
            collection=collection,
            count=len(records),
        )

    async def query(
        self,
        collection: str,
        query_text: str,
        *,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[MemoryQueryResult]:
        chroma_collection = self._get_collection(collection)

        try:
            embed_result = await self._model_router.embed([query_text])
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"Failed to embed query text: {exc}"
            ) from exc

        try:
            raw = chroma_collection.query(
                query_embeddings=cast(
                    Embeddings,
                    embed_result.vectors,
                ),
                n_results=top_k,
                where=metadata_filter or None,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"ChromaDB query failed for collection '{collection}': {exc}"
            ) from exc

        results: list[MemoryQueryResult] = []

        raw_ids = raw.get("ids")
        raw_documents = raw.get("documents")
        raw_metadatas = raw.get("metadatas")
        raw_distances = raw.get("distances")

        ids = raw_ids[0] if raw_ids else []
        documents = raw_documents[0] if raw_documents else []
        metadatas = raw_metadatas[0] if raw_metadatas else []
        distances = raw_distances[0] if raw_distances else []

        for rid, doc, meta, dist in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=True,
        ):
            score = (
                1.0 - dist
                if self._config.distance_metric == "cosine"
                else -dist
            )

            record = MemoryRecord(
                id=rid,
                text=doc or "",
                metadata=dict(meta or {}),
            )

            results.append(
                MemoryQueryResult(
                    record=record,
                    score=score,
                )
            )

        return results

    async def delete(self, collection: str, record_ids: list[str]) -> None:
        if not record_ids:
            return

        chroma_collection = self._get_collection(collection)

        try:
            chroma_collection.delete(ids=record_ids)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"ChromaDB delete failed: {exc}"
            ) from exc

    async def delete_collection(self, collection: str) -> None:
        name = build_collection_name(
            self._config.collection_prefix,
            collection,
        )

        try:
            self._client.delete_collection(name=name)
            self._collection_cache.pop(name, None)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"ChromaDB collection delete failed: {exc}"
            ) from exc

    async def get_by_id(
        self,
        collection: str,
        record_id: str,
    ) -> MemoryRecord | None:
        chroma_collection = self._get_collection(collection)

        try:
            raw = chroma_collection.get(
                ids=[record_id],
                include=["documents", "metadatas"],
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"ChromaDB get failed: {exc}"
            ) from exc

        ids = raw.get("ids", [])

        if not ids:
            return None

        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])

        return MemoryRecord(
            id=ids[0],
            text=documents[0] if documents else "",
            metadata=(
                dict(metadatas[0])
                if metadatas and metadatas[0]
                else {}
            ),
        )

    @staticmethod
    def _sanitize_metadata(
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """ChromaDB metadata values must be str/int/float/bool — coerce anything else."""

        sanitized: dict[str, Any] = {}

        for key, value in metadata.items():
            if isinstance(value, str | int | float | bool):
                sanitized[key] = value
            elif value is None:
                continue
            else:
                sanitized[key] = str(value)

        return sanitized