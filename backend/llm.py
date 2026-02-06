"""Local LLM integration via Ollama."""
from __future__ import annotations

import requests

from config import settings


def generate_completion(prompt: str) -> str:
    """Send a prompt to the local Ollama server and return the response."""

    response = requests.post(
        f"{settings.ollama_url}/api/generate",
        json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("response", "")
