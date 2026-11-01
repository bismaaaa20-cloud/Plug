"""Explicit provider registry."""

from plug.errors import UnknownProviderError
from plug.providers.base import Provider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, provider: Provider) -> None:
        name = getattr(provider, "name", None)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("provider must expose a non-empty name")
        if name in self._providers:
            raise ValueError(f"provider {name!r} is already registered")
        self._providers[name] = provider

    def get(self, name: str) -> Provider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise UnknownProviderError(f"provider {name!r} is not registered") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
