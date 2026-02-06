"""SQLite-backed vector store for offline embeddings."""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class Document:
    """Representation of an indexed document."""

    doc_id: str
    content: str
    metadata: dict
    embedding: np.ndarray


class VectorStore:
    """A lightweight vector database built on SQLite."""

    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    embedding_dim INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_documents(self, documents: Iterable[Document]) -> int:
        """Insert or replace documents in the store."""

        rows = []
        for doc in documents:
            embedding = np.asarray(doc.embedding, dtype=np.float32)
            rows.append(
                (
                    doc.doc_id,
                    doc.content,
                    json.dumps(doc.metadata),
                    embedding.tobytes(),
                    embedding.shape[-1],
                )
            )
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO documents (doc_id, content, metadata, embedding, embedding_dim)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    content=excluded.content,
                    metadata=excluded.metadata,
                    embedding=excluded.embedding,
                    embedding_dim=excluded.embedding_dim
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def get_all_documents(self) -> list[Document]:
        """Return all documents stored in the database."""

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT doc_id, content, metadata, embedding, embedding_dim FROM documents"
            ).fetchall()
        documents = []
        for doc_id, content, metadata_json, embedding_blob, embedding_dim in rows:
            embedding = np.frombuffer(embedding_blob, dtype=np.float32).reshape(-1, embedding_dim)
            documents.append(
                Document(
                    doc_id=doc_id,
                    content=content,
                    metadata=json.loads(metadata_json),
                    embedding=embedding[0],
                )
            )
        return documents

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        """Return top-k similar documents using cosine similarity."""

        docs = self.get_all_documents()
        if not docs:
            return []
        embeddings = np.stack([doc.embedding for doc in docs])
        query = query_embedding.astype(np.float32)
        if query.ndim == 2:
            query = query[0]
        denom = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query)
        denom[denom == 0] = 1.0
        scores = (embeddings @ query) / denom
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            doc = docs[idx]
            results.append(
                {
                    "id": doc.doc_id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": float(scores[idx]),
                }
            )
        return results
