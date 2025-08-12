"""Add documents and their embeddings to a ChromaDB collection."""


from .embed import get_embeddings
from .initializers import get_client


def add_documents(collection_name: str, documents: list[str], ids: list[str]) -> None:
    if len(documents) != len(ids):
        raise ValueError("documents and ids must be the same length")

    collection = get_client().get_or_create_collection(collection_name)
    collection.add(
        documents=documents,
        embeddings=get_embeddings(documents),
        ids=ids,
    )
    print(f"✅ {len(documents)} documents added to collection '{collection_name}'.")
