from pathlib import Path

import pandas as pd

from .models import Document


def load_csv(path: str | Path, **read_csv_kwargs) -> list[Document]:
    """Load a CSV as row-oriented Documents.

    Row-level documents are useful for learning structured-data ingestion and
    preserve the source row number. Later we can compare this with table-level
    and chunk-level strategies.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    frame = pd.read_csv(file_path, **read_csv_kwargs)
    documents: list[Document] = []

    for row_number, row in frame.iterrows():
        values = [f"{column}: {row[column]}" for column in frame.columns]
        content = "\n".join(values)
        documents.append(
            Document(
                content=content,
                metadata={
                    "source_type": "csv",
                    "source": str(file_path.resolve()),
                    "file_name": file_path.name,
                    "row_number": int(row_number) + 2,
                    "columns": list(frame.columns),
                },
                id=f"{file_path.resolve()}#row={row_number + 2}",
            )
        )

    return documents
