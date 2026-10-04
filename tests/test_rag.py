from utils.rag.chunker import chunk_text
from utils.rag.metadata import build_document_metadata
from utils.rag.vector_store import VectorStore


def test_chunk_text_basic():
    text = "a " * 200
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 0
    assert all(c.strip() for c in chunks)


def test_build_metadata():
    metadata = build_document_metadata({"id": "s1", "name": "Test Source", "url": "https://example.com"}, "/tmp/test.txt", "Doc Title")
    assert metadata["source_id"] == "s1"
    assert metadata["source_name"] == "Test Source"


def test_empty_vector_store_diagnostic(tmp_path):
    store = VectorStore(str(tmp_path / "chroma"))
    report = store.diagnostics()

    assert report["collection_name"] == "sangyan_sahayak"
    assert report["document_count"] == 0
    assert report["embedding_available"] is False
    assert report["sample_metadata"] is None
    assert report["persist_directory"] == str((tmp_path / "chroma").resolve())
