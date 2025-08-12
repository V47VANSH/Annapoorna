"""ChromaDB client, created on first use."""

import threading

from chromadb import HttpClient
from chromadb.config import Settings

import config

# no type hint: HttpClient is a function, so "HttpClient | None" fails
_client = None
_lock = threading.Lock()

api_url = config.EMBEDDINGS_API_URL


class VectorStoreUnavailable(RuntimeError):
    """CHROMA_HOST isn't set."""


def get_client():
    """Connect on first use."""
    global _client
    if _client is not None:
        return _client

    if not config.CHROMA_HOST:
        raise VectorStoreUnavailable(
            "CHROMA_HOST is not configured. Set it to your ChromaDB endpoint."
        )

    with _lock:
        if _client is None:
            _client = HttpClient(
                host=config.CHROMA_HOST,
                settings=Settings(allow_reset=True, anonymized_telemetry=False),
            )
    return _client
