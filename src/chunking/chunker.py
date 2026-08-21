from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..ingestion.adls import create_adls_service_client, list_paths, read_text, upload_text


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


def _document_fingerprint(document: dict[str, Any]) -> str:
    """Use the strongest source fingerprint already produced by ingestion."""
    metadata = document.get("metadata", {})
    return (
        metadata.get("record_hash")
        or metadata.get("row_hash")
        or metadata.get("content_hash")
        or metadata.get("file_hash")
        or _sha256(document.get("content", ""))
    )


def chunk_text(content: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
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
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Convert one normalized Document JSON object into Chunk objects."""
    document_id = document["id"]
    metadata = dict(document.get("metadata", {}))
    contents = chunk_text(document.get("content", ""), chunk_size, chunk_overlap)

    chunks: list[Chunk] = []
    for index, content in enumerate(contents):
        chunk_id = _sha256(f"{document_id}:{index}:{content}")[:32]
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


class ChunkingState:
    """Small local checkpoint store used by the learning implementation."""

    def __init__(self, path: str | Path = "metadata/chunking_state.json") -> None:
        self.path = Path(path)
        self.data: dict[str, Any] = self._read()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def get(self, document_id: str) -> dict[str, Any] | None:
        return self.data.get(document_id)

    def put(self, document_id: str, fingerprint: str, chunks: list[Chunk], chunk_size: int, chunk_overlap: int) -> None:
        self.data[document_id] = {
            "document_id": document_id,
            "content_fingerprint": fingerprint,
            "chunking_strategy": "fixed_word_window",
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunk_count": len(chunks),
            "status": "success",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }


def process_document(
    document: dict[str, Any],
    state: ChunkingState,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[str, list[Chunk]]:
    """Chunk only when content or chunking configuration changed."""
    document_id = document["id"]
    fingerprint = _document_fingerprint(document)
    previous = state.get(document_id)

    if (
        previous
        and previous.get("content_fingerprint") == fingerprint
        and previous.get("chunk_size") == chunk_size
        and previous.get("chunk_overlap") == chunk_overlap
        and previous.get("chunking_strategy") == "fixed_word_window"
    ):
        return "skipped_unchanged", []

    chunks = chunk_document(document, chunk_size, chunk_overlap)
    state.put(document_id, fingerprint, chunks, chunk_size, chunk_overlap)
    return "processed", chunks


def process_adls(
    storage_account: str,
    file_system: str,
    processed_root: str = "processed",
    chunks_root: str = "chunks",
    state_path: str = "metadata/chunking_state.json",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict[str, int]:
    """Read normalized Documents from ADLS and persist chunk artifacts."""
    client = create_adls_service_client(storage_account)
    state = ChunkingState(state_path)
    stats = {"documents_found": 0, "processed": 0, "skipped": 0, "chunks_created": 0}

    paths = [path for path in list_paths(client, file_system, processed_root) if path.endswith(".json")]

    for path in paths:
        document = json.loads(read_text(client, file_system, path))
        if not document.get("id") or "content" not in document:
            continue

        stats["documents_found"] += 1
        status, chunks = process_document(document, state, chunk_size, chunk_overlap)
        if status == "skipped_unchanged":
            stats["skipped"] += 1
            continue

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
        upload_text(client, file_system, output_path, json.dumps(payload, indent=2, ensure_ascii=False))

    state.save()
    return stats
