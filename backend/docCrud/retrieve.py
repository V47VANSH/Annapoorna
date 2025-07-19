from typing import List
import nltk
from itertools import chain
from initializers import client, api_url
from embed import get_embeddings

# Download sentence tokenizer if not already
nltk.download('punkt')

def chunk_text(text: str, max_tokens: int = 50, overlap: int = 10) -> List[str]:
    """Chunk text into overlapping segments for large queries."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + max_tokens]
        chunks.append(" ".join(chunk))
        i += max_tokens - overlap
    return chunks

def retrieve(collectionName: str, query: str, api_url: str, top_k: int = 4) -> List[str]:
    """
    Retrieves relevant documents for a possibly long query by chunking and merging.
    """

    # 1. Chunk the query
    print("✅ Chunking query...")
    query_chunks = chunk_text(query, max_tokens=50, overlap=10)

    # 2. Embed all chunks
    print("✅ Getting embeddings...")
    chunk_embeddings = get_embeddings(query_chunks, api_url)

    # 3. Get the collection
    print("✅ Getting collection...")
    collection = client.get_or_create_collection(collectionName)

    # 4. Query for each chunk
    print("✅ Querying chunks...")
    results = [
        collection.query(query_embeddings=[emb], n_results=top_k)
        for emb in chunk_embeddings
    ]

    # 5. Flatten and deduplicate results
    all_docs = list(chain.from_iterable(r["documents"][0] for r in results))
    seen = set()
    unique_docs = []
    for doc in all_docs:
        if doc not in seen:
            seen.add(doc)
            unique_docs.append(doc)
        if len(unique_docs) >= top_k:
            break

    return unique_docs


docs = retrieve("all-my-documents", "Raspberries are known to grow in tropical areas. They are often red coloured and taste tangy!", api_url)
print("\n".join(docs))
