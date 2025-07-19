from typing import List
from initializers import client, api_url
from embed import get_embeddings


def add_documents(collection_name: str, documents: List[str], ids: List[str]):
    """
    Adds documents and their embeddings to the ChromaDB collection.
    """
    collection = client.get_or_create_collection(collection_name)

    embeddings = get_embeddings(documents, api_url)

    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids
    )
    print(f"✅ {len(documents)} documents added to collection '{collection_name}'.")


# Example usage
if __name__ == "__main__":
    docs = [
        "Quantum computing will revolutionize problem-solving.",
        "Climate change is a major global issue.",
        "Embeddings help transform text into numerical vectors."
    ]
    ids = [f"doc_{i}" for i in range(len(docs))]

    add_documents("all-my-documents", docs, ids)
