from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .client import get_chroma_collection


def _find_first_embedding_file(root: str = "embeddings") -> Path:
    """Find one local embedding artifact for the first ingestion exercise."""
    files = sorted(Path(root).rglob("*.json"))
    if not files:
        raise FileNotFoundError(f"No embedding JSON files found under {root!r}")
    return files[0]


def load_first_embedding(path: str | None = None) -> dict[str, Any]:
    """Load one embedding artifact and return its first embedded chunk."""
    embedding_path = Path(path) if path else _find_first_embedding_file()
    payload = json.loads(embedding_path.read_text(encoding="utf-8"))

    embeddings = payload.get("embeddings", [])
    if not embeddings:
        raise ValueError(f"Embedding artifact contains no embeddings: {embedding_path}")

    record = embeddings[0]
    if not record.get("chunk_id"):
        raise ValueError("Embedding record is missing chunk_id")
    if not record.get("document_id"):
        raise ValueError("Embedding record is missing document_id")

    vector = record.get("embedding")
    if not isinstance(vector, list) or len(vector) != int(payload.get("embedding_dimension", 0)):
        raise ValueError("Embedding vector is missing or has the wrong dimension")

    return record


def ingest_one(path: str | None = None) -> int:
    """Insert exactly one embedding record into the Chroma collection."""
    record = load_first_embedding(path)
    collection = get_chroma_collection()

    collection.upsert(
        ids=[record["chunk_id"]],
        embeddings=[record["embedding"]],
        documents=[record["content"]],
        metadatas=[record.get("metadata", {})],
    )

    return collection.count()


def main() -> None:
    count = ingest_one()
    print("One embedding inserted successfully")
    print(f"Vectors: {count}")


if __name__ == "__main__":
    main()
