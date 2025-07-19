import requests
from typing import List
def get_embeddings(texts: List[str], api_url: str) -> List[List[float]]:
    response = requests.post(api_url, json={
        "model": "openai/clip-vit-base-patch32",
        "input": texts
    })
    response.raise_for_status()
    return [item["embedding"] for item in response.json()["data"]]