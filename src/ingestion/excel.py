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


def _document_id(source_id: str, sheet_name: str, row_id: str) -> str:
    return _sha256(f"{source_id}#sheet={sheet_name}#row={row_id}".encode("utf-8"))[:32]


def load_excel(path: str | Path, persist_to_adls: bool = False, storage_account: str | None = None,
                file_system: str | None = None, state_path: str | Path = "metadata/ingestion_state/excel_state.json",
                raw_root: str = "raw", processed_root: str = "processed", row_key: str | None = None) -> list[Document]:
    """Incremental Excel ingestion with workbook, sheet and row-level state."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ValueError(f"Unsupported Excel extension: {file_path.suffix}")

    raw_bytes = file_path.read_bytes()
    if not raw_bytes:
        raise ValueError(f"Excel file is empty: {file_path}")

    file_hash = _sha256(raw_bytes)
    source_id = str(file_path.resolve())
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
        raw_path = f"{raw_root}/excel/{file_path.name}"
        upload_bytes(client, file_system, raw_path, raw_bytes)

    sheets = pd.read_excel(file_path, sheet_name=None)
    previous_rows = previous.rows if previous else {}
    current_rows: dict[str, dict] = {}
    documents: list[Document] = []
    counts = {"new": 0, "changed": 0, "unchanged": 0, "deleted": 0}

    for sheet_name, frame in sheets.items():
        if frame.empty:
            continue
        columns = [str(column) for column in frame.columns]
        if row_key and row_key not in columns:
            raise ValueError(f"row_key '{row_key}' is not present in sheet '{sheet_name}' columns: {columns}")

        seen: set[str] = set()
        for row_number, row in frame.iterrows():
            if row_key:
                value = row[row_key]
                if pd.isna(value) or str(value).strip() == "":
                    raise ValueError(f"Missing row key '{row_key}' in sheet '{sheet_name}' at row {row_number + 2}")
                row_id = str(value).strip()
            else:
                row_id = _row_hash(row, columns)

            state_id = f"{sheet_name}::{row_id}"
            if state_id in seen:
                raise ValueError(f"Duplicate row identity '{row_id}' in sheet '{sheet_name}'")
            seen.add(state_id)
            row_hash = _row_hash(row, columns)
            current_rows[state_id] = {"sheet_name": sheet_name, "row_id": row_id, "row_hash": row_hash,
                                      "row_number": int(row_number) + 2, "status": "success"}

            previous_row = previous_rows.get(state_id)
            if previous_row and previous_row.get("row_hash") == row_hash:
                counts["unchanged"] += 1
                continue

            status = "changed" if previous_row else "new"
            counts[status] += 1
            content = "\n".join(f"{column}: {row[column]}" for column in columns)
            document = Document(content=content, metadata={
                "source_type": "excel", "source": source_id, "file_name": file_path.name,
                "sheet_name": sheet_name, "row_number": int(row_number) + 2, "row_id": row_id,
                "row_hash": row_hash, "file_hash": file_hash, "columns": columns,
                "ingestion_status": status,
            }, id=_document_id(source_id, sheet_name, row_id))
            if raw_path:
                document.metadata["raw_path"] = raw_path
                document.metadata["processed_path"] = f"{processed_root}/excel/{document.id}.json"
            documents.append(document)
            if client:
                upload_text(client, file_system, f"{processed_root}/excel/{document.id}.json",
                            json.dumps(asdict(document), indent=2, ensure_ascii=False))

    deleted = sorted(set(previous_rows) - set(current_rows)) if previous else []
    for state_id in deleted:
        current_rows[state_id] = {**previous_rows[state_id], "status": "deleted"}
    counts["deleted"] = len(deleted)

    state_store.upsert(IngestionFileState(source_id=source_id, file_hash=file_hash, status="success",
                                          processed_at=state_store.now(), rows=current_rows))
    print("Ingestion status: processed")
    print(f"File SHA-256: {file_hash}")
    print(f"Sheets read: {len(sheets)}")
    print(f"Rows read: {sum(len(frame) for frame in sheets.values())}")
    print(f"New: {counts['new']}")
    print(f"Changed: {counts['changed']}")
    print(f"Unchanged: {counts['unchanged']}")
    print(f"Deleted: {counts['deleted']}")
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Excel with incremental sheet/row change detection")
    parser.add_argument("path")
    parser.add_argument("--persist-to-adls", action="store_true")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--file-system", default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"))
    parser.add_argument("--state-path", default="metadata/ingestion_state/excel_state.json")
    parser.add_argument("--row-key", default=None)
    args = parser.parse_args()
    documents = load_excel(args.path, args.persist_to_adls, args.storage_account, args.file_system,
                            args.state_path, row_key=args.row_key)
    for document in documents:
        print("\n--- Document ---")
        print(f"ID: {document.id}")
        print(f"Metadata: {document.metadata}")
        print(f"Content:\n{document.content}")


if __name__ == "__main__":
    main()
