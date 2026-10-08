import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    chroma_persist_directory: str = "./data/chroma"
    top_k_retrieval: int = 6
    max_upload_mb: int = 10
    chat_max_output_tokens: int = 1200
    app_env: str = "development"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing. Add it to your .env file.")

        return cls(
            gemini_api_key=api_key,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
            gemini_embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip() or "gemini-embedding-001",
            chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma").strip() or "./data/chroma",
            top_k_retrieval=int(os.getenv("TOP_K_RETRIEVAL", "6").strip() or "6"),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10").strip() or "10"),
            chat_max_output_tokens=max(
                256, int(os.getenv("CHAT_MAX_OUTPUT_TOKENS", "1200").strip() or "1200")
            ),
            app_env=os.getenv("APP_ENV", "development").strip() or "development",
            log_level=os.getenv("LOG_LEVEL", "INFO").strip() or "INFO",
        )


try:
    settings = Settings.from_env()
except ValueError:
    # Don't crash at import time; app.py / API show a clear message when the key is missing.
    settings = Settings(gemini_api_key="")


def ensure_directories() -> None:
    Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
    Path("./data/uploads").mkdir(parents=True, exist_ok=True)