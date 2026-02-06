# LocalForge

LocalForge is an **offline-first AI development environment** that keeps your code, embeddings, and AI workflows fully local. It pairs a Python backend that talks to a local LLM (Ollama) with a React-based IDE-style frontend featuring a file explorer, Monaco editor, embedding search, and local AI assistant.

## Features

- **Local LLM integration** via Ollama for summarization, suggestions, and Q&A.
- **Offline vector database** using SQLite + embeddings for code search.
- **Local indexing workflows** (server-side path indexing or browser-based file import).
- **Privacy-first**: no external API calls, all data stays on your machine.
- **Docker-ready** for optional local container deployment.

## Architecture

```
frontend (React + Monaco)  -->  backend (FastAPI)
                                   |-> SQLite vector store
                                   |-> local embeddings (sentence-transformers)
                                   |-> local LLM (Ollama)
```

## Requirements

- Python 3.11+
- Node.js 18+ (for frontend)
- [Ollama](https://ollama.com/) running locally (offline) with a downloaded model

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Offline Embeddings

- By default, the backend uses `sentence-transformers/all-MiniLM-L6-v2`.
- For fully offline usage, download the model once and set:

```bash
export EMBEDDING_MODEL_PATH=/path/to/local/model
```

If `sentence-transformers` is unavailable, the backend falls back to a hashing vectorizer (still offline, but lower quality).

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Using the Frontend

1. Select a local folder using the **Project Files** picker.
2. Click **Index in LocalForge** to embed and store your files.
3. Use **Embedding Search** to query the indexed code.
4. Ask the **Local LLM Assistant** for summaries or suggestions.

## Example Scripts

```bash
python backend/scripts/index_project.py /path/to/project
python backend/scripts/query_llm.py "Summarize the indexing workflow"
```

## API Endpoints

- `POST /index`: Index files from a local path on the backend host.
- `POST /add-batch`: Add documents from the frontend or scripts.
- `POST /search`: Search indexed content by embedding similarity.
- `POST /query`: Retrieve context + query the local LLM.

## Docker (Optional)

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:4173`

> Ensure Ollama is running on the host with your model downloaded. The compose file uses `host.docker.internal` so the backend can reach your host Ollama server.

## Offline Workflow Tips

- Download your Ollama model while online, then disconnect.
- Download the sentence-transformers model to `EMBEDDING_MODEL_PATH` before going offline.
- Keep your code, embeddings, and queries on-device.

## Roadmap Ideas

- Add filesystem watching for automatic background indexing.
- Add multi-project workspaces and saved sessions.
- Add inline code actions driven by the local LLM.
