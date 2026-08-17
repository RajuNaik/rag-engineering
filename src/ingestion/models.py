from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Document:
    """Common object returned by ingestion loaders.

    ``content`` is intentionally kept as source content at this stage. Later
    parsing/normalization and chunking stages will operate on this object.
    ``metadata`` preserves provenance and source-specific information.
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("Document.content must be a string")
        if self.id is None:
            self.id = self.metadata.get("source")
