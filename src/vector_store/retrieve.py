from __future__ import annotations

from .client import get_chroma_collection


CHUNK_ID = "b4be6539f0625695cf8f97937d622738"


def main() -> None:
    collection = get_chroma_collection()

    result = collection.get(
        ids=[CHUNK_ID],
        include=["documents", "metadatas", "embeddings"],
    )

    print("IDs:")
    print(result["ids"])

    print("\nDocument:")
    print(result["documents"])

    print("\nMetadata:")
    print(result["metadatas"])

    print("\nEmbedding dimensions:")
    if result["embeddings"]:
        print(len(result["embeddings"][0]))
    else:
        print(0)


if __name__ == "__main__":
    main()
