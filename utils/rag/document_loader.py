from __future__ import annotations

import io
import logging
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pypdf

logger = logging.getLogger(__name__)
MAX_SOURCE_BYTES = 15 * 1024 * 1024


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
        if not self._skip_depth:
            self.text_parts.append(cleaned)


def _extract_pages(payload: bytes, content_type: str, source_name: str) -> tuple[str, list[dict[str, Any]]]:
    if "pdf" in content_type.lower() or payload.startswith(b"%PDF"):
        reader = pypdf.PdfReader(io.BytesIO(payload))
        pages = [
            {"text": page.extract_text() or "", "page_number": index + 1}
            for index, page in enumerate(reader.pages)
        ]
        title = source_name
        metadata = reader.metadata
        if metadata and metadata.title:
            title = metadata.title
        return title, pages

    parser = _HTMLTextExtractor()
    parser.feed(payload.decode("utf-8", errors="replace"))
    title = " ".join(parser.title_parts).strip() or source_name
    return title, [{"text": "\n".join(parser.text_parts), "page_number": None}]


def load_text_document(path: str) -> str:
    """Load text or PDF bytes from a local path, preserving page boundaries for PDFs."""
    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    suffix = document_path.suffix.lower()
    if suffix in {".txt", ".md", ".json"}:
        return document_path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        reader = pypdf.PdfReader(str(document_path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported document type: {suffix}")


def _fetch_source(url: str, allowed_domain: str) -> tuple[bytes, str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    domain = allowed_domain.lower().lstrip(".")
    if parsed.scheme != "https" or not (host == domain or host.endswith(f".{domain}")):
        raise ValueError("Source URL must use HTTPS on its configured official domain.")

    request = Request(
        url,
        headers={"User-Agent": "SangyanSahayakKnowledgeSync/1.0"},
    )
    with urlopen(request, timeout=25) as response:
        payload = response.read(MAX_SOURCE_BYTES + 1)
        content_type = response.headers.get("Content-Type", "")
    if len(payload) > MAX_SOURCE_BYTES:
        raise ValueError("Official source exceeds the configured download limit.")
    if not payload:
        raise ValueError("Official source returned an empty response.")
    return payload, content_type


def load_registry_documents(source_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for source in source_registry:
        if source.get("enabled", True) is False:
            continue
        try:
            if source.get("local_path"):
                path = Path(source["local_path"])
                if not path.exists():
                    raise FileNotFoundError(f"Configured source file is missing: {path}")
                suffix = path.suffix.lower()
                if suffix == ".pdf":
                    reader = pypdf.PdfReader(str(path))
                    pages = [
                        {"text": page.extract_text() or "", "page_number": index + 1}
                        for index, page in enumerate(reader.pages)
                    ]
                    title = reader.metadata.title if reader.metadata and reader.metadata.title else source.get("name", path.stem)
                    documents.append({"source": source, "path": str(path), "title": title, "pages": pages})
                else:
                    documents.append(
                        {
                            "source": source,
                            "path": str(path),
                            "title": source.get("name", path.stem),
                            "pages": [{"text": load_text_document(str(path)), "page_number": None}],
                        }
                    )
                continue

            url = source.get("url")
            domain = source.get("allowed_domain")
            if not url or not domain:
                raise ValueError("Remote source requires a URL and allowed_domain.")
            payload, content_type = _fetch_source(url, domain)
            title, pages = _extract_pages(payload, content_type, source.get("name", "Official document"))
            documents.append(
                {
                    "source": source,
                    "path": url,
                    "title": title,
                    "pages": pages,
                }
            )
        except Exception as exc:
            logger.warning(
                "knowledge_source_fetch_failed source_id=%s error_type=%s",
                source.get("id", "unknown"),
                type(exc).__name__,
            )
            continue
    return documents
