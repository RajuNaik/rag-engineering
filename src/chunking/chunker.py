from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from ..ingestion.adls import create_adls_service_client, list_paths, read_text, upload_text


# Learning defaults: intentionally small so chunk boundaries are easy to inspect.
# Production values will be supplied by configuration rather than hard-coded here.
DEFAULT_CHUNK_SIZE = 10
DEFAULT_CHUNK_OVERLAP = 2


@dataclass(slots=True)
class Chunk:
    """A retrieval unit produced from one normalized Document."""

    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: dict[str, Any]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(
    content: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Create deterministic word-based chunks while preserving overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

    words = re.findall(r"\S+", content)
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    step = chunk_size - chunk_overlap

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += step

    return chunks


def chunk_document(
    document: dict[str, Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Convert one normalized Document JSON object into Chunk objects."""
    document_id = document["id"]
    metadata = dict(document.get("metadata", {}))
    contents = chunk_text(document.get("content", ""), chunk_size, chunk_overlap)

    chunks: list[Chunk] = []
    for index, content in enumerate(contents):
        # Chunk ID is deterministic for this parent document + position + content.
        chunk_id = _sha256(f"{document_id}:{index}:{content}")[:32]

        # Chunk hash describes the exact chunk content. It is not used as a
        # checkpoint here; the ingestion layer has already filtered unchanged data.
        chunk_metadata = {
            **metadata,
            "document_id": document_id,
            "chunk_index": index,
            "chunk_hash": _sha256(content),
            "chunking_strategy": "fixed_word_window",
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        chunks.append(
            Chunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=index,
                content=content,
                metadata=chunk_metadata,
            )
        )

    return chunks


def process_document(
    document: dict[str, Any],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Chunk a Document supplied by the upstream incremental ingestion stage."""
    return chunk_document(document, chunk_size, chunk_overlap)


def process_adls(
    storage_account: str,
    file_system: str,
    processed_root: str = "processed",
    chunks_root: str = "chunks",
    document_path: str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict[str, int]:
    """Chunk Documents supplied by the upstream ingestion/checkpoint layer.

    In production, the preferred mode is document_path: the upstream event/orchestrator
    passes only the newly created or changed processed Document. We deliberately do not
    maintain a second content fingerprint/checkpoint here.
    """
    client = create_adls_service_client(storage_account)
    stats = {"documents_found": 0, "processed": 0, "chunks_created": 0}

    if document_path:
        paths = [document_path]
    else:
        # Batch mode is retained for local learning/backfill. It intentionally processes
        # every processed Document supplied to it; production orchestration should pass
        # document_path for incremental execution.
        paths = [
            path
            for path in list_paths(client, file_system, processed_root)
            if path.endswith(".json")
        ]

    for path in paths:
        document = json.loads(read_text(client, file_system, path))
        if not document.get("id") or "content" not in document:
            continue

        stats["documents_found"] += 1
        chunks = process_document(document, chunk_size, chunk_overlap)
        stats["processed"] += 1
        stats["chunks_created"] += len(chunks)

        source_type = document.get("metadata", {}).get("source_type", "unknown")
        output_path = f"{chunks_root}/{source_type}/{document['id']}.json"
        payload = {
            "document_id": document["id"],
            "source_document": path,
            "chunk_count": len(chunks),
            "chunks": [asdict(chunk) for chunk in chunks],
        }
        upload_text(
            client,
            file_system,
            output_path,
            json.dumps(payload, indent=2, ensure_ascii=False),
        )

    return stats
