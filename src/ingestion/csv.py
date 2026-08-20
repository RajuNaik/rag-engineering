from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .adls import create_adls_service_client, upload_bytes, upload_text
from .models import Document
from .state import IngestionFileState, IngestionStateStore

load_dotenv()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _row_hash(row: pd.Series, columns: list[str]) -> str:
    values = ["" if pd.isna(row[column]) else str(row[column]).strip() for column in columns]
    return _sha256("\x1f".join(values).encode("utf-8"))


def _source_id(path: Path) -> str:
    return str(path.resolve())


def _document_id(source_id: str, row_id: str) -> str:
    return _sha256(f"{source_id}#row={row_id}".encode("utf-8"))[:32]


def load_csv(
    path: str | Path,
    persist_to_adls: bool = False,
    storage_account: str | None = None,
    file_system: str | None = None,
    state_path: str | Path = "metadata/ingestion_state/csv_state.json",
    raw_root: str = "raw",
    processed_root: str = "processed",
    row_key: str | None = None,
    **read_csv_kwargs,
) -> list[Document]:
    """Incremental CSV ingestion with file and row-level change detection."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.suffix.lower() != ".csv":
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")

    raw_bytes = file_path.read_bytes()
    if not raw_bytes:
        raise ValueError(f"CSV file is empty: {file_path}")

    file_hash = _sha256(raw_bytes)
    source_id = _source_id(file_path)
    state_store = IngestionStateStore(state_path)
    previous = state_store.get(source_id)

    if previous and previous.file_hash == file_hash and previous.status == "success":
        print("Ingestion status: skipped_unchanged")
        return []

    client = None
    raw_path = None
    if persist_to_adls:
        if not storage_account or not file_system:
            raise ValueError("storage_account and file_system are required when persist_to_adls=True")
        client = create_adls_service_client(storage_account)
        raw_path = f"{raw_root}/csv/{file_path.name}"
        upload_bytes(client, file_system, raw_path, raw_bytes)

    frame = pd.read_csv(file_path, **read_csv_kwargs)
    if frame.empty:
        raise ValueError(f"CSV contains no data rows: {file_path}")

    columns = [str(column) for column in frame.columns]
    if row_key and row_key not in columns:
        raise ValueError(f"row_key '{row_key}' is not present in CSV columns: {columns}")

    previous_rows = previous.rows if previous else {}
    current_rows: dict[str, dict] = {}
    documents: list[Document] = []

    for row_number, row in frame.iterrows():
        if row_key:
            value = row[row_key]
            if pd.isna(value) or str(value).strip() == "":
                raise ValueError(f"Missing row key '{row_key}' at CSV row {row_number + 2}")
            row_id = str(value).strip()
        else:
            row_id = _row_hash(row, columns)

        row_hash = _row_hash(row, columns)
        current_rows[row_id] = {
            "row_hash": row_hash,
            "row_number": int(row_number) + 2,
            "status": "success",
        }

        previous_row = previous_rows.get(row_id)
        if previous_row and previous_row.get("row_hash") == row_hash:
            continue

        content = "\n".join(f"{column}: {row[column]}" for column in columns)
        document = Document(
            content=content,
            metadata={
                "source_type": "csv",
                "source": source_id,
                "file_name": file_path.name,
                "row_number": int(row_number) + 2,
                "row_id": row_id,
                "row_hash": row_hash,
                "file_hash": file_hash,
                "columns": columns,
                "ingestion_status": "changed" if previous_row else "new",
            },
            id=_document_id(source_id, row_id),
        )
        if raw_path:
            document.metadata["raw_path"] = raw_path
            document.metadata["processed_path"] = f"{processed_root}/csv/{document.id}.json"
        documents.append(document)

        if client:
            upload_text(
                client,
                file_system,
                f"{processed_root}/csv/{document.id}.json",
                json.dumps(asdict(document), indent=2, ensure_ascii=False),
            )

    deleted_rows = sorted(set(previous_rows) - set(current_rows)) if previous else []
    for row_id in deleted_rows:
        current_rows[row_id] = {
            "row_hash": previous_rows[row_id].get("row_hash"),
            "status": "deleted",
            "row_number": previous_rows[row_id].get("row_number"),
        }

    state_store.upsert(
        IngestionFileState(
            source_id=source_id,
            file_hash=file_hash,
            status="success",
            processed_at=state_store.now(),
            rows=current_rows,
        )
    )

    print("Ingestion status: processed")
    print(f"File SHA-256: {file_hash}")
    print(f"Rows read: {len(frame)}")
    print(f"Documents created/changed: {len(documents)}")
    print(f"Rows deleted: {len(deleted_rows)}")
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CSV with incremental file/row change detection")
    parser.add_argument("path")
    parser.add_argument("--persist-to-adls", action="store_true")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--file-system", default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"))
    parser.add_argument("--state-path", default="metadata/ingestion_state/csv_state.json")
    parser.add_argument("--row-key", default=None, help="Stable business key column, e.g. EmployeeID")
    args = parser.parse_args()

    documents = load_csv(
        args.path,
        persist_to_adls=args.persist_to_adls,
        storage_account=args.storage_account,
        file_system=args.file_system,
        state_path=args.state_path,
        row_key=args.row_key,
    )

    for document in documents:
        print("\n--- Document ---")
        print(f"ID: {document.id}")
        print(f"Metadata: {document.metadata}")
        print(f"Content:\n{document.content}")


if __name__ == "__main__":
    main()
