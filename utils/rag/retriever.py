from __future__ import annotations

import logging
from typing import Any

from utils.ai.gemini_client import GeminiClient
from utils.config import settings
from utils.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, vector_store: VectorStore | None = None, client: GeminiClient | None = None) -> None:
        self.vector_store = vector_store or VectorStore()
        self.client = client or GeminiClient()

    def retrieve_relevant_documents(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        top_k = settings.top_k_retrieval if top_k is None else top_k
        logger.debug(
            "rag_retrieval_started query_characters=%d top_k=%d source_filter=%s",
            len(query),
            top_k,
            None,
        )
        embedding = self.client.embed_text(query)
        logger.debug("rag_query_embedding_created dimensions=%d", len(embedding))
        results = self.vector_store.query(embedding, top_k=top_k)
        items: list[dict[str, Any]] = []
        document_groups = results.get("documents") or []
        metadata_groups = results.get("metadatas") or []
        distance_groups = results.get("distances") or []
        docs = document_groups[0] if document_groups else []
        metadatas = metadata_groups[0] if metadata_groups else []
        distances = distance_groups[0] if distance_groups else []
        for index, document in enumerate(docs):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else None
            relevance = 1 / (1 + max(float(distance), 0.0)) if distance is not None else None
            items.append({
                "content": document,
                "metadata": metadata,
                "distance": distance,
                "relevance": relevance,
            })
        logger.debug(
            "rag_retrieval_completed retrieved_count=%d scores=%s",
            len(items),
            [
                {
                    "source_id": item["metadata"].get("source_id"),
                    "distance": item["distance"],
                    "relevance": item["relevance"],
                }
                for item in items
            ],
        )
        return items
