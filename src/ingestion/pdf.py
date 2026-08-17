from pathlib import Path

from pypdf import PdfReader

from .models import Document


def load_pdf(path: str | Path) -> list[Document]:
    """Load a PDF as one Document per page while preserving page metadata."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    reader = PdfReader(str(file_path))
    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        documents.append(
            Document(
                content=text,
                metadata={
                    "source_type": "pdf",
                    "source": str(file_path.resolve()),
                    "file_name": file_path.name,
                    "page_number": page_number,
                    "total_pages": len(reader.pages),
                },
                id=f"{file_path.resolve()}#page={page_number}",
            )
        )

    return documents
