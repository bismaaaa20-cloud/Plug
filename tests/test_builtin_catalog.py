from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from plug.builtin_catalog import (
    PLUGIN_DEFINITIONS,
    SKILL_DEFINITIONS,
    install_builtin_catalog,
    run_builtin,
)
from plug.plugins.registry import PluginRegistry
from plug.skills.loader import SkillRegistry


class BuiltinCatalogTests(unittest.TestCase):
    def test_catalog_has_exactly_25_plugins_and_25_skills(self):
        self.assertEqual(len(PLUGIN_DEFINITIONS), 25)
        self.assertEqual(len(SKILL_DEFINITIONS), 25)
        self.assertEqual(len({item[0] for item in PLUGIN_DEFINITIONS}), 25)
        self.assertEqual(len({item[0] for item in SKILL_DEFINITIONS}), 25)

    def test_installer_materializes_all_items_and_discovery_finds_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugin_root, skill_root = root / "plugins", root / "skills"
            result = install_builtin_catalog(plugin_root, skill_root)
            self.assertEqual(result["plugins"], 25)
            self.assertEqual(result["skills"], 25)
            self.assertEqual(len(list(plugin_root.glob("*/plugin.json"))), 25)
            self.assertEqual(len(list(skill_root.glob("*/SKILL.md"))), 25)
            self.assertEqual(len(list(skill_root.glob("*/scripts/main.py"))), 25)
            plugins = PluginRegistry()
            plugins.discover(plugin_root)
            self.assertEqual(len(plugins.names()), 25)
            skills = SkillRegistry()
            skills.discover(skill_root)
            self.assertEqual(len(skills.names()), 25)

    def test_all_plugin_handlers_execute(self):
        samples = {
            "text-stats": {"text": "one two\nthree"},
            "text-clean": {"text": "  hello  "},
            "text-slug": {"text": "Hello Plug!"},
            "text-extract": {"text": "visit https://example.com"},
            "json-format": {"json": {"ok": True}},
            "json-query": {"data": {"a": {"b": 3}}, "path": "a.b"},
            "csv-stats": {"csv": "name,age\nAda,36\n"},
            "csv-filter": {"csv": "name,age\nAda,36\n", "column": "name", "equals": "Ada"},
            "math-calc": {"expression": "2 + 3 * 4"},
            "datetime-convert": {"value": "2026-01-01T12:00:00+00:00"},
            "uuid-generate": {"count": 2},
            "text-hash": {"text": "hello"},
            "base64-encode": {"text": "hello"},
            "base64-decode": {"base64": "aGVsbG8="},
            "url-encode": {"text": "hello world"},
            "regex-match": {"pattern": r"\\d+", "text": "a12b"},
            "text-diff": {"before": "old\n", "after": "new\n"},
            "files-list": {"path": "."},
            "files-read": {"path": __file__},
            "files-write": {"path": str(Path(tempfile.gettempdir()) / "plug-catalog-test.txt"), "text": "ok"},
            "archive-inspect": {"path": __file__},
            "python-check": {"source": "x = 1"},
            "xml-parse": {"xml": "<root><child /></root>"},
            "html-extract": {"html": "<title>Test</title><p>Hello</p>"},
            "url-parse": {"url": "https://example.com/path"},
        }
        class Context:
            def __init__(self, plugin_id):
                self.plugin_id = plugin_id
            def require(self, permission):
                return None
        for plugin_id, *_ in PLUGIN_DEFINITIONS:
            with self.subTest(plugin=plugin_id):
                result = run_builtin(Context(plugin_id), samples[plugin_id])
                self.assertIsNotNone(result)

    def test_safe_calculator_rejects_code_execution(self):
        with self.assertRaises((ValueError, SyntaxError)):
            run_builtin(SimpleNamespace(plugin_id="math-calc"), {"expression": "__import__('os').system('echo unsafe')"})

    def test_installer_refuses_to_overwrite_existing_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugins, skills = root / "plugins", root / "skills"
            install_builtin_catalog(plugins, skills)
            with self.assertRaises(FileExistsError):
                install_builtin_catalog(plugins, skills)


if __name__ == "__main__":
    unittest.main()
