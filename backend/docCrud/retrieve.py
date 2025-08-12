"""Retrieve relevant documents for a query, chunking long inputs first."""

from itertools import chain

from .embed import get_embeddings
from .initializers import get_client


def chunk_text(text: str, max_words: int = 50, overlap: int = 10) -> list[str]:
    """Split text into overlapping chunks of words."""
    if overlap >= max_words:
        raise ValueError("overlap must be smaller than max_words")

    words = text.split()
    if not words:
        return []

    chunks = []
    step = max_words - overlap
    for i in range(0, len(words), step):
        chunks.append(" ".join(words[i : i + max_words]))
        if i + max_words >= len(words):
            break
    return chunks


def retrieve(
    collection_name: str,
    query: str,
    api_url: str | None = None,
    top_k: int = 4,
) -> list[str]:
    """Return up to ``top_k`` unique documents most relevant to ``query``."""
    query_chunks = chunk_text(query)
    if not query_chunks:
        return []

    chunk_embeddings = get_embeddings(query_chunks, api_url)
    collection = get_client().get_or_create_collection(collection_name)

    results = [
        collection.query(query_embeddings=[embedding], n_results=top_k)
        for embedding in chunk_embeddings
    ]

    all_docs = chain.from_iterable(result["documents"][0] for result in results)

    seen = set()
    unique_docs = []
    for doc in all_docs:
        if doc in seen:
            continue
        seen.add(doc)
        unique_docs.append(doc)
        if len(unique_docs) >= top_k:
            break

    return unique_docs
