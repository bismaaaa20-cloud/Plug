"""Environment-backed settings with no external dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    max_concurrency: int = 4
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        raw_concurrency = os.getenv("PLUG_MAX_CONCURRENCY", "4")
        try:
            concurrency = int(raw_concurrency)
        except ValueError as exc:
            raise ValueError("PLUG_MAX_CONCURRENCY must be an integer") from exc
        if concurrency < 1:
            raise ValueError("PLUG_MAX_CONCURRENCY must be positive")
        level = os.getenv("PLUG_LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("PLUG_LOG_LEVEL is invalid")
        return cls(max_concurrency=concurrency, log_level=level)
