from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from ..ingestion.adls import create_adls_service_client, list_paths, read_text
from .client import get_chroma_collection


load_dotenv()


def _get_adls_config() -> tuple[str, str, str]:
    """Read the existing ADLS configuration used by the ingestion/embedding layers."""
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
    file_system = os.getenv("AZURE_STORAGE_FILE_SYSTEM")
    embeddings_root = os.getenv("AZURE_STORAGE_EMBEDDINGS_ROOT", "embeddings")

    if not storage_account or not file_system:
        raise ValueError(
            "AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_FILE_SYSTEM are required"
        )

    return storage_account, file_system, embeddings_root


def _find_first_embedding_path(
    client: Any,
    file_system: str,
    embeddings_root: str,
) -> str:
    """Find one embedding artifact directly from ADLS for the first ingestion exercise."""
    paths = sorted(
        path
        for path in list_paths(client, file_system, embeddings_root)
        if path.endswith(".json")
    )

    if not paths:
        raise FileNotFoundError(
            f"No embedding JSON files found under ADLS path {embeddings_root!r}"
        )

    return paths[0]


def load_first_embedding(
    client: Any,
    file_system: str,
    embedding_path: str,
) -> dict[str, Any]:
    """Download one embedding artifact from ADLS and return its first embedded chunk."""
    payload = json.loads(read_text(client, file_system, embedding_path))

    embeddings = payload.get("embeddings", [])
    if not embeddings:
        raise ValueError(f"Embedding artifact contains no embeddings: {embedding_path}")

    record = embeddings[0]
    if not record.get("chunk_id"):
        raise ValueError("Embedding record is missing chunk_id")
    if not record.get("document_id"):
        raise ValueError("Embedding record is missing document_id")

    vector = record.get("embedding")
    expected_dimension = int(payload.get("embedding_dimension", 0))
    if not isinstance(vector, list) or len(vector) != expected_dimension:
        raise ValueError(
            f"Embedding vector is missing or has the wrong dimension: "
            f"expected {expected_dimension}, got {len(vector) if isinstance(vector, list) else 0}"
        )

    return record


def ingest_one() -> int:
    """POC: read one embedding from ADLS and insert exactly one vector into Chroma."""
    storage_account, file_system, embeddings_root = _get_adls_config()
    adls_client = create_adls_service_client(storage_account)
    embedding_path = _find_first_embedding_path(
        adls_client,
        file_system,
        embeddings_root,
    )
    record = load_first_embedding(adls_client, file_system, embedding_path)

    collection = get_chroma_collection()

    collection.upsert(
        ids=[record["chunk_id"]],
        embeddings=[record["embedding"]],
        documents=[record["content"]],
        metadatas=[record.get("metadata", {})],
    )

    print(f"Embedding source: {embedding_path}")
    print(f"Chunk ID: {record['chunk_id']}")

    return collection.count()


def main() -> None:
    # POC: intentionally ingest only one embedding record.
    # Production will discover and process new embedding artifacts incrementally.
    count = ingest_one()
    print("One embedding inserted successfully")
    print(f"Vectors: {count}")


if __name__ == "__main__":
    main()
