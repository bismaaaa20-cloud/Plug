"""Small SQLite-backed, local-only memory store with lexical retrieval."""

from __future__ import annotations

import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

_WORD = re.compile(r"[a-z0-9_+-]+", re.IGNORECASE)


def _tokens(value: str) -> set[str]:
    return {item.lower() for item in _WORD.findall(value)}


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    id: str
    content: str
    category: str
    created_at: float


class MemoryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, content TEXT NOT NULL, "
                "category TEXT NOT NULL, created_at REAL NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def remember(self, content: str, *, category: str = "general") -> MemoryRecord:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("memory content must not be empty")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("memory category must not be empty")
        record = MemoryRecord(uuid.uuid4().hex, content.strip(), category.strip(), time.time())
        with self._connect() as connection:
            connection.execute("INSERT INTO memories VALUES (?, ?, ?, ?)",
                               (record.id, record.content, record.category, record.created_at))
        return record

    def search(self, query: str, *, limit: int = 5) -> tuple[MemoryRecord, ...]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if limit < 1:
            raise ValueError("limit must be positive")
        terms = _tokens(query)
        if not terms:
            return ()
        with self._connect() as connection:
            rows = connection.execute("SELECT id, content, category, created_at FROM memories").fetchall()
        ranked = []
        for row in rows:
            content_terms = _tokens(row["content"] + " " + row["category"])
            score = len(terms & content_terms)
            if score:
                ranked.append((score, row["created_at"], MemoryRecord(row["id"], row["content"], row["category"], row["created_at"])))
        ranked.sort(key=lambda item: (-item[0], -item[1]))
        return tuple(item[2] for item in ranked[:limit])

    def delete(self, memory_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0
