from __future__ import annotations

from utils.ai.gemini_client import GeminiClient


class EmbeddingProvider:
    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    def embed(self, text: str) -> list[float]:
        return self.client.embed_text(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed_texts(texts)
