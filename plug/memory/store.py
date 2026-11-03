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
        clean_content, clean_category = content.strip(), category.strip()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id, content, category, created_at FROM memories "
                "WHERE content = ? AND category = ? ORDER BY created_at DESC LIMIT 1",
                (clean_content, clean_category),
            ).fetchone()
            if existing:
                return MemoryRecord(
                    existing["id"], existing["content"], existing["category"], existing["created_at"]
                )
            record = MemoryRecord(uuid.uuid4().hex, clean_content, clean_category, time.time())
            connection.execute(
                "INSERT INTO memories VALUES (?, ?, ?, ?)",
                (record.id, record.content, record.category, record.created_at),
            )
        return record

    def search(self, query: str, *, limit: int = 5) -> tuple[MemoryRecord, ...]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
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

    def recall_context(
        self, query: str, *, max_tokens: int = 256, limit: int = 5
    ) -> str:
        """Build a small prompt-ready memory block without loading full history.

        Uses a conservative UTF-8-bytes/3 estimate and includes complete records
        only, so the budget is never met by cutting a memory mid-sentence.
        """
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer")
        records = self.search(query, limit=limit)
        prefix = "Relevant project memory:\n"
        lines: list[str] = []
        for record in records:
            line = f"- [{record.category}] {record.content}"
            candidate = prefix + "\n".join((*lines, line))
            estimate = max(1, (len(candidate.encode("utf-8")) + 2) // 3)
            if estimate > max_tokens:
                continue
            lines.append(line)
        if not lines:
            return ""
        return prefix + "\n".join(lines)

    def delete(self, memory_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0
