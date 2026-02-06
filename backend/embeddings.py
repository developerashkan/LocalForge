"""Embedding utilities supporting offline models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import importlib.util

import numpy as np

from config import settings

SentenceTransformer = None
if importlib.util.find_spec("sentence_transformers"):
    from sentence_transformers import SentenceTransformer  # type: ignore

HashingVectorizer = None
if importlib.util.find_spec("sklearn.feature_extraction.text"):
    from sklearn.feature_extraction.text import HashingVectorizer  # type: ignore


@dataclass
class Embedder:
    """Wrapper for embedding generation with a consistent API."""

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        raise NotImplementedError


@dataclass
class SentenceTransformerEmbedder(Embedder):
    """Embedder powered by a local sentence-transformers model."""

    model: SentenceTransformer

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        embeddings = self.model.encode(list(texts), show_progress_bar=False)
        return np.asarray(embeddings, dtype=np.float32)


@dataclass
class HashingEmbedder(Embedder):
    """Fallback embedder using a hashing vectorizer (fully offline)."""

    vectorizer: HashingVectorizer

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        matrix = self.vectorizer.transform(list(texts))
        dense = matrix.toarray().astype(np.float32)
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return dense / norms


def get_embedder() -> Embedder:
    """Return the best available embedder for the current environment."""

    if SentenceTransformer is not None:
        model_name = settings.embedding_model_path or "sentence-transformers/all-MiniLM-L6-v2"
        model = SentenceTransformer(model_name)
        return SentenceTransformerEmbedder(model=model)

    if HashingVectorizer is None:
        raise RuntimeError(
            "No embedding backend available. Install sentence-transformers or scikit-learn."
        )

    vectorizer = HashingVectorizer(n_features=512, alternate_sign=False, norm=None)
    return HashingEmbedder(vectorizer=vectorizer)
