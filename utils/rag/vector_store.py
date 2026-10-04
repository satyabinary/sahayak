from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence
from typing import Any

import chromadb
import numpy as np
from chromadb.api.types import Metadata, QueryResult

from utils.config import settings


class VectorStore:
    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name="sangyan_sahayak")

    def add_documents(self, ids: list[str], documents: list[str], metadatas: Sequence[Metadata], embeddings: list[list[float]]) -> None:
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=list(metadatas),
            embeddings=np.asarray(embeddings, dtype=np.float32),
        )

    def upsert_documents(self, ids: list[str], documents: list[str], metadatas: Sequence[Metadata], embeddings: list[list[float]]) -> None:
        if not ids:
            return
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=list(metadatas),
            embeddings=np.asarray(embeddings, dtype=np.float32),
        )

    def query(self, query_embedding: list[float], top_k: int = 6) -> QueryResult:
        count = self.count()
        if count == 0 or top_k <= 0:
            return {
                "ids": [[]],
                "embeddings": None,
                "documents": [[]],
                "uris": None,
                "data": None,
                "metadatas": [[]],
                "distances": [[]],
                "included": ["documents", "metadatas", "distances"],
            }
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        try:
            self.client.delete_collection(name="sangyan_sahayak")
        except Exception:  # pragma: no cover
            pass
        self.collection = self.client.get_or_create_collection(name="sangyan_sahayak")

    def get_status(self) -> dict[str, Any]:
        return {
            "collection_name": "sangyan_sahayak",
            "persist_directory": self.persist_directory,
            "count": self.count(),
        }

    def diagnostics(self) -> dict[str, Any]:
        """Return safe index health details without exposing stored document text or vectors."""
        count = self.count()
        sample = self.collection.get(
            limit=1,
            include=["metadatas", "embeddings"] if count else ["metadatas"],
        )
        embeddings = sample.get("embeddings")
        embedding_available = bool(
            count
            and embeddings is not None
            and len(embeddings) > 0
            and len(embeddings[0]) > 0
        )
        metadata = sample.get("metadatas") or []
        return {
            "collection_name": self.collection.name,
            "document_count": count,
            "embedding_available": embedding_available,
            "sample_metadata": metadata[0] if metadata else None,
            "persist_directory": str(Path(self.persist_directory).resolve()),
        }
