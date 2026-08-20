from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class IngestionFileState:
    """Persistent file-level and row-level ingestion metadata for local learning."""

    source_id: str
    file_hash: str
    status: str
    processed_at: str
    rows: dict[str, dict[str, Any]]


class IngestionStateStore:
    """Small JSON-backed state store.

    Production systems can replace this implementation with a Delta/SQL/NoSQL
    store without changing the ingestion decision logic.
    """

    def __init__(self, path: str | Path = "metadata/ingestion_state/csv_state.json") -> None:
        self.path = Path(path)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def get(self, source_id: str) -> IngestionFileState | None:
        record = self._read().get(source_id)
        if not record:
            return None
        return IngestionFileState(**record)

    def upsert(self, state: IngestionFileState) -> None:
        data = self._read()
        data[state.source_id] = asdict(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()
