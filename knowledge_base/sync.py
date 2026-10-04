from __future__ import annotations

import logging

from utils.rag.ingestion import KnowledgeBaseIngestor

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


def sync_knowledge_base() -> dict[str, object]:
    ingestor = KnowledgeBaseIngestor()
    summary = ingestor.ingest()
    print(summary)
    return summary


if __name__ == "__main__":
    sync_knowledge_base()
