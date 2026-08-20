from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .adls import create_adls_service_client, upload_bytes, upload_text
from .models import Document
from .state import IngestionFileState, IngestionStateStore

load_dotenv()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(
    path: str | Path,
    persist_to_adls: bool = False,
    storage_account: str | None = None,
    file_system: str | None = None,
    state_path: str | Path = "metadata/ingestion_state/json_state.json",
    raw_root: str = "raw",
    processed_root: str = "processed",
) -> list[Document]:
    """Load one JSON source as one logical Document.

    This first JSON implementation deliberately preserves the complete parsed
    structure. Document splitting/semantic normalization comes later.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.suffix.lower() != ".json":
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")

    raw_bytes = file_path.read_bytes()
    if not raw_bytes:
        raise ValueError(f"JSON file is empty: {file_path}")

    file_hash = _sha256(raw_bytes)
    source_id = str(file_path.resolve())
    state_store = IngestionStateStore(state_path)
    previous = state_store.get(source_id)

    if previous and previous.file_hash == file_hash and previous.status == "success":
        print("Ingestion status: skipped_unchanged")
        return []

    try:
        parsed: Any = json.loads(raw_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"JSON must be UTF-8: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {file_path}: {exc}") from exc

    document_id = _sha256(source_id.encode("utf-8"))[:32]
    content = json.dumps(parsed, indent=2, ensure_ascii=False)

    client = None
    raw_path = None
    processed_path = None
    if persist_to_adls:
        if not storage_account or not file_system:
            raise ValueError("storage_account and file_system are required when persist_to_adls=True")
        client = create_adls_service_client(storage_account)
        raw_path = f"{raw_root}/json/{file_path.name}"
        processed_path = f"{processed_root}/json/{document_id}.json"
        upload_bytes(client, file_system, raw_path, raw_bytes)

    document = Document(
        id=document_id,
        content=content,
        metadata={
            "source_type": "json",
            "source": source_id,
            "file_name": file_path.name,
            "file_hash": file_hash,
            "ingestion_status": "changed" if previous else "new",
            "raw_path": raw_path,
            "processed_path": processed_path,
        },
    )

    if client and processed_path:
        upload_text(
            client,
            file_system,
            processed_path,
            json.dumps(asdict(document), indent=2, ensure_ascii=False),
        )

    state_store.upsert(
        IngestionFileState(
            source_id=source_id,
            file_hash=file_hash,
            status="success",
            processed_at=state_store.now(),
            rows={
                "document": {
                    "row_hash": file_hash,
                    "status": "success",
                    "document_id": document_id,
                }
            },
        )
    )

    print("Ingestion status: processed")
    print(f"Document ID: {document.id}")
    print(f"File SHA-256: {file_hash}")
    print(f"Raw ADLS path: {raw_path}")
    print(f"Processed ADLS path: {processed_path}")
    return [document]


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a JSON file as one logical Document")
    parser.add_argument("path")
    parser.add_argument("--persist-to-adls", action="store_true")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--file-system", default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"))
    parser.add_argument("--state-path", default="metadata/ingestion_state/json_state.json")
    args = parser.parse_args()

    documents = load_json(
        args.path,
        persist_to_adls=args.persist_to_adls,
        storage_account=args.storage_account,
        file_system=args.file_system,
        state_path=args.state_path,
    )

    for document in documents:
        print("\n--- Document ---")
        print(f"ID: {document.id}")
        print(f"Metadata: {document.metadata}")
        print(f"Content:\n{document.content}")


if __name__ == "__main__":
    main()
