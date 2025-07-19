from initializers import client
from typing import List

def delete_documents(collection_name: str, ids: List[str]):
    collection = client.get_or_create_collection(collection_name)
    collection.delete(ids=ids)
    print(f"🗑️ Deleted documents with IDs: {ids}")

def delete_all_documents(collection_name: str):
    collection = client.get_or_create_collection(collection_name)
    all_ids = collection.get()['ids']
    if all_ids:
        collection.delete(ids=all_ids)
        print(f"🧹 Cleared all {len(all_ids)} documents from '{collection_name}' collection.")
    else:
        print(f"ℹ️ No documents to delete in '{collection_name}'.")

# Example usage
if __name__ == "__main__":
    # To delete specific documents
    # delete_documents("my_documents", ["doc_0", "doc_1"])

    # To delete all documents
    delete_all_documents("all-my-documents")
