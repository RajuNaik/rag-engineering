from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from .embedding import DEFAULT_BATCH_SIZE, DEFAULT_MODEL_NAME, process_adls


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create embeddings from persisted RAG chunk artifacts")
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT"))
    parser.add_argument("--file-system", default=os.getenv("AZURE_STORAGE_FILE_SYSTEM"))
    parser.add_argument("--chunks-root", default=os.getenv("AZURE_STORAGE_CHUNKS_ROOT", "chunks"))
    parser.add_argument("--embeddings-root", default=os.getenv("AZURE_STORAGE_EMBEDDINGS_ROOT", "embeddings"))
    parser.add_argument("--model", default=os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_MODEL_NAME))
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", DEFAULT_BATCH_SIZE)))
    args = parser.parse_args()

    if not args.storage_account or not args.file_system:
        parser.error("storage account and file system are required")
    if args.batch_size <= 0:
        parser.error("batch size must be greater than zero")

    stats = process_adls(
        storage_account=args.storage_account,
        file_system=args.file_system,
        chunks_root=args.chunks_root,
        embeddings_root=args.embeddings_root,
        model_name=args.model,
        batch_size=args.batch_size,
    )

    print(f"Chunk files found: {stats['files_found']}")
    print(f"Chunk files embedded: {stats['files_embedded']}")
    print(f"Embeddings created: {stats['embeddings_created']}")


if __name__ == "__main__":
    main()
