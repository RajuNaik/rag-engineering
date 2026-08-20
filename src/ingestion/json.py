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


def _canonical_json(value: Any) -> str:
    """Stable JSON representation so equivalent objects hash consistently."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _record_hash(record: dict[str, Any]) -> str:
    return _sha256(_canonical_json(record).encode("utf-8"))


def _document_id(source_id: str, record_id: str) -> str:
    return _sha256(f"{source_id}|employee:{record_id}".encode("utf-8"))[:32]


def load_json(
    path: str | Path,
    persist_to_adls: bool = False,
    storage_account: str | None = None,
    file_system: str | None = None,
    state_path: str | Path = "metadata/ingestion_state/json_state.json",
    raw_root: str = "raw",
    processed_root: str = "processed",
) -> list[Document]:
    """Incrementally ingest a JSON employee collection using employee_id as identity."""
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

    if not isinstance(parsed, dict) or not isinstance(parsed.get("employees"), list):
        raise ValueError("Expected JSON object containing an 'employees' array")

    records: dict[str, dict[str, Any]] = {}
    for record in parsed["employees"]:
        if not isinstance(record, dict):
            raise ValueError("Each employee must be a JSON object")
        if "employee_id" not in record:
            raise ValueError("Each employee must contain employee_id")
        record_id = str(record["employee_id"])
        if record_id in records:
            raise ValueError(f"Duplicate employee_id: {record_id}")
        records[record_id] = record

    previous_rows = previous.rows if previous else {}
    changed_ids: list[str] = []
    new_ids: list[str] = []
    unchanged_ids: list[str] = []
    deleted_ids = sorted(set(previous_rows) - set(records))

    for record_id, record in records.items():
        current_hash = _record_hash(record)
        old = previous_rows.get(record_id)
        if old and old.get("row_hash") == current_hash and old.get("status") == "success":
            unchanged_ids.append(record_id)
        else:
            changed_ids.append(record_id)
            if old is None:
                new_ids.append(record_id)

    client = None
    raw_path = None
    if persist_to_adls:
        if not storage_account or not file_system:
            raise ValueError("storage_account and file_system are required when persist_to_adls=True")
        client = create_adls_service_client(storage_account)
        raw_path = f"{raw_root}/json/{file_path.name}"
        upload_bytes(client, file_system, raw_path, raw_bytes)

    documents: list[Document] = []
    processed_paths: dict[str, str] = {}
    for record_id in changed_ids:
        record = records[record_id]
        document_id = _document_id(source_id, record_id)
        record_hash = _record_hash(record)
        processed_path = f"{processed_root}/json/{document_id}.json"
        processed_paths[record_id] = processed_path
        document = Document(
            id=document_id,
            content=json.dumps(record, indent=2, ensure_ascii=False),
            metadata={
                "source_type": "json",
                "source": source_id,
                "file_name": file_path.name,
                "record_id": record_id,
                "record_hash": record_hash,
                "file_hash": file_hash,
                "ingestion_status": "new" if record_id in new_ids else "changed",
                "raw_path": raw_path,
                "processed_path": processed_path,
            },
        )
        documents.append(document)

        if client:
            upload_text(
                client,
                file_system,
                processed_path,
                json.dumps(asdict(document), indent=2, ensure_ascii=False),
            )

    state_rows: dict[str, dict[str, Any]] = {}
    for record_id, record in records.items():
        state_rows[record_id] = {
            "row_hash": _record_hash(record),
            "status": "success",
            "document_id": _document_id(source_id, record_id),
        }
    for record_id in deleted_ids:
        state_rows[record_id] = {
            "row_hash": previous_rows[record_id].get("row_hash"),
            "status": "deleted",
            "document_id": previous_rows[record_id].get("document_id"),
        }

    state_store.upsert(
        IngestionFileState(
            source_id=source_id,
            file_hash=file_hash,
            status="success",
            processed_at=state_store.now(),
            rows=state_rows,
        )
    )

    print("Ingestion status: processed")
    print(f"File SHA-256: {file_hash}")
    print(f"Records read: {len(records)}")
    print(f"New: {len(new_ids)}")
    print(f"Changed: {len(changed_ids) - len(new_ids)}")
    print(f"Unchanged: {len(unchanged_ids)}")
    print(f"Deleted: {len(deleted_ids)}")
    for document in documents:
        print("\n--- Document ---")
        print(f"ID: {document.id}")
        print(f"Metadata: {document.metadata}")
        print(f"Content:\n{document.content}")

    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Incrementally ingest employee records from JSON")
    parser.add_argument("path")
    parser.add_argument("--persist-to-adls", action="store_true")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--file-system", default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"))
    parser.add_argument("--state-path", default="metadata/ingestion_state/json_state.json")
    args = parser.parse_args()

    load_json(
        args.path,
        persist_to_adls=args.persist_to_adls,
        storage_account=args.storage_account,
        file_system=args.file_system,
        state_path=args.state_path,
    )


if __name__ == "__main__":
    main()
