"""Configuration helpers for LocalForge backend."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Runtime configuration loaded from environment variables."""

    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    embedding_model_path: str | None = os.getenv("EMBEDDING_MODEL_PATH")
    db_path: str = os.getenv("VECTOR_DB_PATH", "./data/embeddings.db")
    auto_index_path: str | None = os.getenv("AUTO_INDEX_PATH")


settings = Settings()
