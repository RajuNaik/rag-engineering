from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

from .adls import create_adls_service_client, upload_bytes, upload_text
from .models import Document

load_dotenv()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _document_id(source: str) -> str:
    """Create a stable document ID from the canonical source path."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:32]


def load_text_file(
    path: str | Path,
    encoding: str = "utf-8",
    persist_to_adls: bool = False,
    storage_account: str | None = None,
    file_system: str | None = None,
    raw_root: str = "raw",
    processed_root: str = "processed",
) -> Document:
    """Ingest a local TXT/Markdown file into the common Document contract.

    With ``persist_to_adls=True`` this follows the production-style learning
    flow: validate → persist raw bytes → extract/normalize → create Document
    → persist processed JSON.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Expected a file, but received: {file_path}")
    if file_path.suffix.lower() not in {".txt", ".md", ".markdown"}:
        raise ValueError(f"Unsupported text file extension: {file_path.suffix}")

    raw_bytes = file_path.read_bytes()
    if not raw_bytes:
        raise ValueError(f"Source file is empty: {file_path}")

    content_hash = _sha256(raw_bytes)
    source = str(file_path.resolve())
    document = Document(
        content=raw_bytes.decode(encoding),
        metadata={
            "source_type": "local_file",
            "source": source,
            "file_name": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "content_hash": content_hash,
            "size_bytes": len(raw_bytes),
        },
        id=_document_id(source),
    )

    if persist_to_adls:
        if not storage_account or not file_system:
            raise ValueError(
                "storage_account and file_system are required when persist_to_adls=True"
            )

        client = create_adls_service_client(storage_account)
        raw_path = f"{raw_root}/txt/{file_path.name}"
        processed_path = f"{processed_root}/txt/{document.id}.json"

        document.metadata.update(
            {
                "raw_path": raw_path,
                "processed_path": processed_path,
                "storage_account": storage_account,
                "file_system": file_system,
            }
        )

        # Raw zone: preserve the exact source bytes for reproducibility/reprocessing.
        upload_bytes(client, file_system, raw_path, raw_bytes)

        # Processed zone: persist the normalized common Document representation.
        processed_json = json.dumps(asdict(document), indent=2, ensure_ascii=False)
        upload_text(client, file_system, processed_path, processed_json)

    return document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a local TXT/Markdown file into the RAG Document contract"
    )
    parser.add_argument("path", help="Path to the TXT/Markdown source file")
    parser.add_argument(
        "--persist-to-adls",
        action="store_true",
        help="Persist raw source and processed Document JSON to ADLS Gen2",
    )
    parser.add_argument(
        "--storage-account",
        default=os.getenv("AZURE_STORAGE_ACCOUNT"),
        help="ADLS storage account; defaults to AZURE_STORAGE_ACCOUNT",
    )
    parser.add_argument(
        "--file-system",
        default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"),
        help="ADLS file system/container; defaults to AZURE_STORAGE_FILE_SYSTEM",
    )
    parser.add_argument(
        "--raw-root",
        default=os.getenv("AZURE_STORAGE_RAW_ROOT", "raw"),
    )
    parser.add_argument(
        "--processed-root",
        default=os.getenv("AZURE_STORAGE_PROCESSED_ROOT", "processed"),
    )
    args = parser.parse_args()

    document = load_text_file(
        args.path,
        persist_to_adls=args.persist_to_adls,
        storage_account=args.storage_account,
        file_system=args.file_system,
        raw_root=args.raw_root,
        processed_root=args.processed_root,
    )

    print(f"Loaded: {document.metadata['file_name']}")
    print(f"Document ID: {document.id}")
    print(f"Characters: {len(document.content)}")
    print(f"Content SHA-256: {document.metadata['content_hash']}")
    if args.persist_to_adls:
        print(f"Raw ADLS path: {document.metadata['raw_path']}")
        print(f"Processed ADLS path: {document.metadata['processed_path']}")
    print(document.content[:500])


if __name__ == "__main__":
    main()
