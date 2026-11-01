"""Small permission-aware interface exposed to local plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class PluginPermissionError(PermissionError):
    """Raised when a plugin requests a capability it was not granted."""


@dataclass(frozen=True, slots=True)
class PluginContext:
    plugin_id: str
    granted_permissions: frozenset[str] = field(default_factory=frozenset)
    settings: dict[str, Any] = field(default_factory=dict)

    def require(self, permission: str) -> None:
        if permission not in self.granted_permissions:
            raise PluginPermissionError(f"plugin {self.plugin_id!r} lacks permission {permission!r}")


@dataclass(frozen=True, slots=True)
class PluginResult:
    ok: bool
    data: Any = None
    message: str = ""
