"""Validated manifest for a trusted local Plug plugin."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


def _string_tuple(data: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = data.get(field_name, ())
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a list of strings")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class PluginManifest:
    id: str
    name: str
    version: str
    description: str
    entrypoint: str
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _PLUGIN_ID.fullmatch(self.id):
            raise ValueError("plugin id must be 2-64 lowercase letters, digits, '_' or '-' and start with a letter")
        for field_name in ("name", "version", "description", "entrypoint"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        entrypoint = self.entrypoint
        if "\\" in entrypoint or "\x00" in entrypoint:
            raise ValueError("entrypoint must use a safe relative POSIX path")
        entry = Path(entrypoint)
        if entry.is_absolute() or ".." in entry.parts or entry.suffix != ".py":
            raise ValueError("entrypoint must be a relative .py file inside the plugin directory")
        for field_name in ("capabilities", "permissions", "keywords"):
            values = tuple(getattr(self, field_name))
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError(f"{field_name} must contain non-empty strings")
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must not contain duplicates")
            object.__setattr__(self, field_name, values)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        if not isinstance(data, dict):
            raise ValueError("plugin manifest must be a JSON object")
        allowed = {"id", "name", "version", "description", "entrypoint", "capabilities", "permissions", "keywords"}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown plugin manifest fields: {sorted(unknown)}")
        return cls(
            id=data.get("id"), name=data.get("name"), version=data.get("version"),
            description=data.get("description"), entrypoint=data.get("entrypoint", "plugin.py"),
            capabilities=_string_tuple(data, "capabilities"),
            permissions=_string_tuple(data, "permissions"),
            keywords=_string_tuple(data, "keywords"),
        )
