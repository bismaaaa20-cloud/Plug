"""Provider protocol and validated request/response values."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from plug.errors import ProviderError


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    prompt: str
    temperature: float = 0.2
    max_tokens: int = 2048

    def __post_init__(self) -> None:
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if isinstance(self.temperature, bool) or not isinstance(self.temperature, (int, float)):
            raise ValueError("temperature must be numeric")
        if not math.isfinite(self.temperature) or self.temperature < 0:
            raise ValueError("temperature must be finite and non-negative")
        if isinstance(self.max_tokens, bool) or not isinstance(self.max_tokens, int) or self.max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer")


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    provider: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if isinstance(self.latency_ms, bool) or not isinstance(self.latency_ms, (int, float)):
            raise ValueError("latency_ms must be numeric")
        if not math.isfinite(self.latency_ms) or self.latency_ms < 0:
            raise ValueError("latency_ms must be finite and non-negative")


@runtime_checkable
class Provider(Protocol):
    name: str

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Generate a response for a request."""

    async def health(self) -> bool:
        """Return whether the provider is ready."""
