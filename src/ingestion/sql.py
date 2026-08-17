from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .models import Document


def create_sql_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine from a database URL."""
    if not database_url:
        raise ValueError("database_url is required")
    return create_engine(database_url, pool_pre_ping=True)


def load_sql_query(engine: Engine, query: str, **params: Any) -> list[Document]:
    """Execute a read-only query and convert rows to Documents.

    Connection credentials and driver details stay outside this module. The
    caller supplies a SQLAlchemy engine, making the loader database-agnostic.
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    with engine.connect() as connection:
        result = connection.execute(text(query), params)
        rows = result.mappings().all()

    documents: list[Document] = []
    for row_number, row in enumerate(rows, start=1):
        content = "\n".join(f"{key}: {value}" for key, value in row.items())
        documents.append(
            Document(
                content=content,
                metadata={
                    "source_type": "sql",
                    "source": "sql_query",
                    "row_number": row_number,
                    "columns": list(row.keys()),
                },
                id=f"sql_query#row={row_number}",
            )
        )

    return documents
