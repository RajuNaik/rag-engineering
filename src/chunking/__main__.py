from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from .chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, process_adls


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk normalized RAG Documents from ADLS")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--file-system", default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"))
    parser.add_argument("--processed-root", default=os.getenv("AZURE_STORAGE_PROCESSED_ROOT", "processed"))
    parser.add_argument("--chunks-root", default=os.getenv("AZURE_STORAGE_CHUNKS_ROOT", "chunks"))
    parser.add_argument("--state-path", default="metadata/chunking_state.json")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    args = parser.parse_args()

    if not args.storage_account or not args.file_system:
        parser.error("storage account and file system are required")

    stats = process_adls(
        storage_account=args.storage_account,
        file_system=args.file_system,
        processed_root=args.processed_root,
        chunks_root=args.chunks_root,
        state_path=args.state_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print(f"Documents found: {stats['documents_found']}")
    print(f"Documents chunked: {stats['processed']}")
    print(f"Documents skipped: {stats['skipped']}")
    print(f"Chunks created: {stats['chunks_created']}")


if __name__ == "__main__":
    main()
