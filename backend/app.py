"""FastAPI application for LocalForge offline AI services."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from embeddings import get_embedder
from llm import generate_completion
from vector_store import Document, VectorStore

app = FastAPI(title="LocalForge Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

embedder = get_embedder()
vector_store = VectorStore(settings.db_path)


class AddItem(BaseModel):
    """Schema for a single document to index."""

    doc_id: str = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="Document text")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AddBatchRequest(BaseModel):
    """Schema for bulk document ingestion."""

    items: list[AddItem]


class SearchRequest(BaseModel):
    """Schema for vector search requests."""

    query: str
    top_k: int = 5


class QueryRequest(BaseModel):
    """Schema for LLM queries with retrieval augmentation."""

    query: str
    top_k: int = 5


class IndexRequest(BaseModel):
    """Schema for indexing a local folder on the backend host."""

    path: str
    extensions: list[str] = Field(default_factory=lambda: [".py", ".js", ".ts", ".md", ".txt"])


@app.on_event("startup")
def _auto_index() -> None:
    """Optionally index a path on startup when AUTO_INDEX_PATH is set."""

    if settings.auto_index_path:
        _index_path(settings.auto_index_path, [".py", ".js", ".ts", ".md", ".txt"])


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health check endpoint."""

    return {"status": "ok"}


@app.post("/add-batch")
def add_batch(request: AddBatchRequest) -> dict[str, int]:
    """Add multiple documents to the vector store."""

    texts = [item.content for item in request.items]
    embeddings = embedder.encode(texts)
    documents = []
    for item, embedding in zip(request.items, embeddings):
        documents.append(
            Document(
                doc_id=item.doc_id,
                content=item.content,
                metadata=item.metadata,
                embedding=embedding,
            )
        )
    count = vector_store.upsert_documents(documents)
    return {"indexed": count}


@app.post("/search")
def search(request: SearchRequest) -> dict[str, Any]:
    """Search indexed documents using embedding similarity."""

    query_embedding = embedder.encode([request.query])
    results = vector_store.search(query_embedding, top_k=request.top_k)
    return {"results": results}


@app.post("/query")
def query(request: QueryRequest) -> dict[str, Any]:
    """Query the local LLM with retrieved context."""

    query_embedding = embedder.encode([request.query])
    results = vector_store.search(query_embedding, top_k=request.top_k)
    context_blocks = "\n\n".join(
        f"Source: {item['id']}\n{item['content']}" for item in results
    )
    prompt = (
        "You are LocalForge, an offline-first coding assistant.\n"
        "Use the context below to answer the user question.\n\n"
        f"Context:\n{context_blocks}\n\n"
        f"Question: {request.query}\nAnswer:"
    )
    response = generate_completion(prompt)
    return {"response": response, "context": results}


@app.post("/index")
def index_path(request: IndexRequest) -> dict[str, int]:
    """Index files from a local path on the backend host."""

    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail="Path not found")
    count = _index_path(request.path, request.extensions)
    return {"indexed": count}


def _index_path(path: str, extensions: list[str]) -> int:
    """Index all supported files from a path."""

    root = Path(path)
    files = [
        file
        for file in root.rglob("*")
        if file.is_file() and file.suffix.lower() in extensions
    ]
    if not files:
        return 0
    contents = []
    items = []
    for file in files:
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        contents.append(content)
        items.append(
            AddItem(
                doc_id=str(file),
                content=content,
                metadata={"path": str(file), "extension": file.suffix.lower()},
            )
        )
    embeddings = embedder.encode(contents)
    documents = []
    for item, embedding in zip(items, embeddings):
        documents.append(
            Document(
                doc_id=item.doc_id,
                content=item.content,
                metadata=item.metadata,
                embedding=embedding,
            )
        )
    return vector_store.upsert_documents(documents)
