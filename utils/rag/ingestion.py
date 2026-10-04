from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import yaml

from utils.ai.gemini_client import GeminiClient
from utils.config import settings
from utils.rag.chunker import chunk_text
from utils.rag.document_loader import load_registry_documents
from utils.rag.embeddings import EmbeddingProvider
from utils.rag.metadata import build_document_metadata
from utils.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class KnowledgeBaseIngestor:
    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.vector_store = VectorStore(self.persist_directory)
        self.embedding_provider = EmbeddingProvider(GeminiClient())

    def load_sources(self) -> list[dict[str, Any]]:
        path = Path("./knowledge_base/sources.yaml")
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data.get("sources", [])

    def _source_is_unchanged(self, source_id: str, document_hash: str) -> bool:
        existing = self.vector_store.collection.get(
            where={"source_id": source_id},
            include=["metadatas"],
        )
        return any(
            metadata.get("document_hash") == document_hash
            for metadata in (existing.get("metadatas") or [])
        )

    def ingest(self) -> dict[str, Any]:
        sources = [source for source in self.load_sources() if source.get("enabled", True)]
        loaded_documents = load_registry_documents(sources)
        loaded_by_id = {item["source"].get("id"): item for item in loaded_documents}
        report: dict[str, Any] = {
            "documents_ingested": 0,
            "documents_skipped": 0,
            "documents_failed": len(sources) - len(loaded_documents),
            "chunks_created": 0,
            "embedding_count": 0,
            "source_results": [],
        }

        for source in sources:
            source_id = source.get("id", "unknown")
            item = loaded_by_id.get(source_id)
            if item is None:
                report["source_results"].append(
                    {"source_id": source_id, "status": "failed", "reason": "source_unavailable"}
                )
                continue

            pages = item["pages"]
            full_text = "\n\n".join(page["text"] for page in pages)
            if not full_text.strip():
                report["documents_failed"] += 1
                report["source_results"].append(
                    {"source_id": source_id, "status": "failed", "reason": "no_extractable_text"}
                )
                continue
            document_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
            if self._source_is_unchanged(source_id, document_hash):
                report["documents_skipped"] += 1
                report["source_results"].append(
                    {"source_id": source_id, "status": "unchanged", "document_hash": document_hash}
                )
                continue

            ids: list[str] = []
            chunks: list[str] = []
            metadatas: list[dict[str, Any]] = []
            embeddings: list[list[float]] = []
            try:
                for page in pages:
                    page_number = page.get("page_number")
                    page_text = page["text"]
                    for chunk_index, chunk in enumerate(
                        chunk_text(page_text, chunk_size=900, overlap=120)
                    ):
                        chunk_id = (
                            f"{source_id}-{document_hash[:12]}-"
                            f"{page_number or 'html'}-{chunk_index}"
                        )
                        metadata = build_document_metadata(
                            source,
                            item["path"],
                            item["title"],
                            {
                                "document_hash": document_hash,
                                "page_number": page_number,
                                "section": None,
                                "retrieved_at": None,
                            },
                        )
                        ids.append(chunk_id)
                        chunks.append(chunk)
                        metadatas.append({**metadata, "chunk_index": chunk_index})
                for offset in range(0, len(chunks), 16):
                    embeddings.extend(
                        self.embedding_provider.embed_many(chunks[offset : offset + 16])
                    )
            except Exception as exc:
                report["documents_failed"] += 1
                logger.error(
                    "knowledge_source_embedding_failed source_id=%s error_type=%s",
                    source_id,
                    type(exc).__name__,
                )
                report["source_results"].append(
                    {"source_id": source_id, "status": "failed", "reason": "embedding_failed"}
                )
                continue

            if not ids:
                report["documents_failed"] += 1
                report["source_results"].append(
                    {"source_id": source_id, "status": "failed", "reason": "no_chunks"}
                )
                continue
            self.vector_store.collection.delete(where={"source_id": source_id})
            self.vector_store.upsert_documents(ids, chunks, metadatas, embeddings)
            report["documents_ingested"] += 1
            report["chunks_created"] += len(chunks)
            report["embedding_count"] += len(embeddings)
            report["source_results"].append(
                {
                    "source_id": source_id,
                    "status": "ingested",
                    "chunks": len(chunks),
                    "document_hash": document_hash,
                }
            )
            logger.info(
                "knowledge_source_ingested source_id=%s chunks=%d",
                source_id,
                len(chunks),
            )

        logger.info(
            "knowledge_sync_finished documents_ingested=%d documents_skipped=%d "
            "documents_failed=%d chunks_created=%d",
            report["documents_ingested"],
            report["documents_skipped"],
            report["documents_failed"],
            report["chunks_created"],
        )
        return report
