from __future__ import annotations

from pathlib import Path
from typing import Any


def build_document_metadata(source: dict[str, Any], document_path: str, title: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = {
        "source_id": source.get("id"),
        "source_name": source.get("name"),
        "source_url": source.get("url"),
        "document_title": title,
        "document_path": str(document_path),
        "publication_date": None,
        "last_updated": None,
        "page_number": None,
        "section": None,
        "document_hash": None,
        "retrieved_at": None,
    }
    if extra:
        metadata.update(extra)
    return metadata
