from __future__ import annotations

from pathlib import Path

import chromadb


DEFAULT_CHROMA_PATH = "vector_store/chroma"
DEFAULT_COLLECTION_NAME = "rag_documents"


def get_chroma_collection(
    path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """Return a persistent Chroma collection, creating it when necessary."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def main() -> None:
    collection = get_chroma_collection()
    print("Chroma collection created successfully")
    print(f"Collection: {collection.name}")
    print(f"Vectors: {collection.count()}")


if __name__ == "__main__":
    main()
