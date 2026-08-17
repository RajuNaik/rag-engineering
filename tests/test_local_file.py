from pathlib import Path

from src.ingestion.local_file import load_text_file


def test_load_text_file(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello RAG", encoding="utf-8")

    document = load_text_file(file_path)

    assert document.content == "hello RAG"
    assert document.metadata["source_type"] == "local_file"
    assert document.metadata["file_name"] == "sample.txt"


def test_load_text_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"

    try:
        load_text_file(missing)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
