"""Delete documents from a ChromaDB collection."""


from .initializers import get_client


def delete_documents(collection_name: str, ids: list[str]) -> None:
    get_client().get_or_create_collection(collection_name).delete(ids=ids)
    print(f"🗑️ Deleted documents with IDs: {ids}")


def delete_all_documents(collection_name: str) -> None:
    collection = get_client().get_or_create_collection(collection_name)
    all_ids = collection.get()["ids"]
    if not all_ids:
        print(f"ℹ️ No documents to delete in '{collection_name}'.")
        return
    collection.delete(ids=all_ids)
    print(f"🧹 Cleared all {len(all_ids)} documents from '{collection_name}'.")
