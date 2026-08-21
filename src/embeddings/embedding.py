from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sentence_transformers import SentenceTransformer

from ..ingestion.adls import create_adls_service_client, list_paths, read_text, upload_text


# Learning model: small, local, open-source and produces 384-dimensional embeddings.
# Production model selection will be configuration/evaluation driven.
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32


@dataclass(slots=True)
class EmbeddedChunk:
    """One chunk plus its embedding and lineage metadata."""

    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    embedding: list[float]
    metadata: dict[str, Any]


def load_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    """Load the local embedding model."""
    return SentenceTransformer(model_name)


def embed_chunk_file(
    chunk_document: dict[str, Any],
    model: SentenceTransformer,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Embed every chunk in one chunk artifact and preserve lineage."""
    chunks = chunk_document.get("chunks", [])
    if not chunks:
        return {
            "document_id": chunk_document.get("document_id"),
            "source_chunk_document": chunk_document.get("source_document"),
            "embedding_count": 0,
            "embeddings": [],
        }

    texts = [chunk["content"] for chunk in chunks]
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    embedded_chunks: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        embedded_chunks.append(
            EmbeddedChunk(
                chunk_id=chunk["id"],
                document_id=chunk["document_id"],
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=vector.astype(float).tolist(),
                metadata=dict(chunk.get("metadata", {})),
            )
        )

    dimension = len(embedded_chunks[0].embedding)
    return {
        "document_id": chunk_document["document_id"],
        "source_chunk_document": chunk_document.get("source_document"),
        "embedding_model": model.get_sentence_embedding_dimension() and model.__class__.__name__ or None,
        "embedding_model_name": getattr(model, "model_card_data", None) and getattr(model.model_card_data, "model_name", None) or DEFAULT_MODEL_NAME,
        "embedding_dimension": dimension,
        "embedding_count": len(embedded_chunks),
        "embeddings": [asdict(item) for item in embedded_chunks],
    }


def process_adls(
    storage_account: str,
    file_system: str,
    chunks_root: str = "chunks",
    embeddings_root: str = "embeddings",
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, int]:
    """POC mode: read every chunk artifact and create one embedding artifact per file."""
    client = create_adls_service_client(storage_account)
    model = load_model(model_name)

    paths = [
        path
        for path in list_paths(client, file_system, chunks_root)
        if path.endswith(".json")
    ]

    stats = {"files_found": len(paths), "files_embedded": 0, "embeddings_created": 0}

    for path in paths:
        chunk_document = json.loads(read_text(client, file_system, path))
        payload = embed_chunk_file(chunk_document, model, batch_size)

        source_type = "unknown"
        chunks = chunk_document.get("chunks", [])
        if chunks:
            source_type = chunks[0].get("metadata", {}).get("source_type", "unknown")

        document_id = chunk_document["document_id"]
        output_path = f"{embeddings_root}/{source_type}/{document_id}.json"
        upload_text(
            client,
            file_system,
            output_path,
            json.dumps(payload, indent=2, ensure_ascii=False),
        )

        stats["files_embedded"] += 1
        stats["embeddings_created"] += payload["embedding_count"]

    return stats
