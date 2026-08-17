from pathlib import Path

from .models import Document


def load_text_file(path: str | Path, encoding: str = "utf-8") -> Document:
    """Load a UTF-8-compatible text/Markdown file into a Document."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding=encoding)
    return Document(
        content=content,
        metadata={
            "source_type": "local_file",
            "source": str(file_path.resolve()),
            "file_name": file_path.name,
            "file_extension": file_path.suffix.lower(),
        },
        id=str(file_path.resolve()),
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load a local text/Markdown file")
    parser.add_argument("path")
    args = parser.parse_args()

    document = load_text_file(args.path)
    print(f"Loaded: {document.metadata['file_name']}")
    print(f"Characters: {len(document.content)}")
    print(document.content[:500])
