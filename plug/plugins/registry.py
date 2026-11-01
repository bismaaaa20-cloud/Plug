"""Discovery and explicit execution of trusted local plugins."""

from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
from typing import Any

from plug.plugins.manifest import PluginManifest
from plug.plugins.sdk import PluginContext, PluginResult


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, tuple[PluginManifest, Path]] = {}
        self._enabled: set[str] = set()

    def discover(self, root: str | Path) -> tuple[str, ...]:
        base = Path(root).resolve()
        if not base.exists():
            return ()
        found: list[str] = []
        for manifest_path in sorted(base.glob("*/plugin.json")):
            plugin_dir = manifest_path.parent.resolve()
            if plugin_dir.parent != base:
                continue
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = PluginManifest.from_dict(data)
            if manifest.id in self._plugins:
                raise ValueError(f"duplicate plugin id: {manifest.id}")
            self._plugins[manifest.id] = (manifest, plugin_dir)
            found.append(manifest.id)
        return tuple(found)

    def get(self, plugin_id: str) -> PluginManifest:
        return self._plugins[plugin_id][0]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._plugins))

    def enable(self, plugin_id: str) -> None:
        if plugin_id not in self._plugins:
            raise KeyError(plugin_id)
        self._enabled.add(plugin_id)

    def disable(self, plugin_id: str) -> None:
        self._enabled.discard(plugin_id)

    def is_enabled(self, plugin_id: str) -> bool:
        return plugin_id in self._enabled

    async def execute(
        self, plugin_id: str, *, granted_permissions: set[str] | frozenset[str] = frozenset(),
        arguments: dict[str, Any] | None = None,
    ) -> PluginResult:
        if plugin_id not in self._plugins:
            raise KeyError(plugin_id)
        if plugin_id not in self._enabled:
            raise PermissionError(f"plugin {plugin_id!r} is not enabled")
        manifest, plugin_dir = self._plugins[plugin_id]
        granted = frozenset(granted_permissions)
        missing = set(manifest.permissions) - granted
        if missing:
            raise PermissionError(f"plugin requires ungranted permissions: {sorted(missing)}")
        entrypoint = (plugin_dir / manifest.entrypoint).resolve()
        if plugin_dir not in entrypoint.parents or not entrypoint.is_file():
            raise ValueError("plugin entrypoint is missing or escapes its directory")
        module_name = f"_plug_plugin_{plugin_id.replace('-', '_')}_{manifest.version.replace('.', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, entrypoint)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load plugin {plugin_id!r}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        runner = getattr(module, "run", None)
        if not callable(runner):
            raise TypeError("plugin entrypoint must expose run(context, arguments)")
        result = runner(PluginContext(plugin_id, granted), arguments or {})
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, PluginResult):
            return result
        return PluginResult(ok=True, data=result)
