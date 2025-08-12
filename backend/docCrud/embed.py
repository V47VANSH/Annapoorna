"""Text embeddings via an OpenAI-compatible embeddings endpoint."""


import requests

import config

EMBEDDINGS_TIMEOUT_SECONDS = 30


def get_embeddings(texts: list[str], api_url: str | None = None) -> list[list[float]]:
    """Embed a batch of strings, returning one vector per input."""
    url = api_url or config.EMBEDDINGS_API_URL
    if not url:
        raise RuntimeError("EMBEDDINGS_API_URL is not configured.")

    response = requests.post(
        url,
        json={"model": config.EMBEDDINGS_MODEL, "input": texts},
        timeout=EMBEDDINGS_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return [item["embedding"] for item in response.json()["data"]]
