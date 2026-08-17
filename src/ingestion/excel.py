from pathlib import Path

import pandas as pd

from .models import Document


def load_excel(path: str | Path, sheet_name: str | int = 0, **read_excel_kwargs) -> list[Document]:
    """Load an Excel worksheet as row-oriented Documents."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    frame = pd.read_excel(file_path, sheet_name=sheet_name, **read_excel_kwargs)
    documents: list[Document] = []

    for row_number, row in frame.iterrows():
        values = [f"{column}: {row[column]}" for column in frame.columns]
        content = "\n".join(values)
        documents.append(
            Document(
                content=content,
                metadata={
                    "source_type": "excel",
                    "source": str(file_path.resolve()),
                    "file_name": file_path.name,
                    "sheet": sheet_name,
                    "row_number": int(row_number) + 2,
                    "columns": list(frame.columns),
                },
                id=f"{file_path.resolve()}#sheet={sheet_name}&row={row_number + 2}",
            )
        )

    return documents
