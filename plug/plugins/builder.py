"""Create a minimal local plugin scaffold without overwriting files."""

from __future__ import annotations

import json
import re
from pathlib import Path


def create_plugin(root: str | Path, plugin_id: str, *, name: str, description: str,
                  permissions: tuple[str, ...] = (), keywords: tuple[str, ...] = ()) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9_-]{1,63}", plugin_id):
        raise ValueError("invalid plugin id")
    target = Path(root) / plugin_id
    target.mkdir(parents=True, exist_ok=False)
    manifest = {
        "id": plugin_id, "name": name, "version": "0.1.0", "description": description,
        "entrypoint": "plugin.py", "capabilities": [], "permissions": list(permissions),
        "keywords": list(keywords),
    }
    (target / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (target / "plugin.py").write_text(
        '"""Plug plugin entrypoint. Only run after reviewing its code and permissions."""\n\n'
        'def run(context, arguments):\n'
        '    # Call context.require("permission-name") before using a protected capability.\n'
        '    return {"plugin": context.plugin_id, "received": arguments}\n', encoding="utf-8"
    )
    return target
