from __future__ import annotations

import asyncio
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from plug.builtin_catalog import (
    PLUGIN_DEFINITIONS,
    SKILL_DEFINITIONS,
    install_builtin_catalog,
    run_builtin,
)
from plug.plugins.registry import PluginRegistry
from plug.skills.loader import SkillRegistry


class BuiltinCatalogTests(unittest.TestCase):
    def test_catalog_has_exactly_175_plugins_and_175_skills(self):
        self.assertEqual(len(PLUGIN_DEFINITIONS), 175)
        self.assertEqual(len(SKILL_DEFINITIONS), 175)
        self.assertEqual(len({item[0] for item in PLUGIN_DEFINITIONS}), 175)
        self.assertEqual(len({item[0] for item in SKILL_DEFINITIONS}), 175)

    def test_installer_materializes_all_items_and_discovery_finds_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugin_root, skill_root = root / "plugins", root / "skills"
            result = install_builtin_catalog(plugin_root, skill_root)
            self.assertEqual(result["plugins"], 175)
            self.assertEqual(result["skills"], 175)
            self.assertEqual(len(list(plugin_root.glob("*/plugin.json"))), 175)
            self.assertEqual(len(list(skill_root.glob("*/SKILL.md"))), 175)
            self.assertEqual(len(list(skill_root.glob("*/scripts/main.py"))), 175)
            plugins = PluginRegistry()
            plugins.discover(plugin_root)
            self.assertEqual(len(plugins.names()), 175)
            skills = SkillRegistry()
            skills.discover(skill_root)
            self.assertEqual(len(skills.names()), 175)

    def test_all_plugin_handlers_execute(self):
        with tempfile.TemporaryDirectory() as archive_dir:
            archive_path = Path(archive_dir) / "sample.zip"
            image_path = Path(archive_dir) / "tiny.png"
            image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + (2).to_bytes(4, "big") + (1).to_bytes(4, "big"))
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("sample.txt", "hello needle")
            (Path(archive_dir) / "copy.txt").write_text("same", encoding="utf-8")
            (Path(archive_dir) / "copy-2.txt").write_text("same", encoding="utf-8")
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
                "files-write": {"path": str(Path(archive_dir) / "written.txt"), "text": "ok"},
                "archive-inspect": {"path": str(archive_path)},
                "python-check": {"source": "x = 1"},
                "xml-parse": {"xml": "<root><child /></root>"},
                "html-extract": {"html": "<title>Test</title><p>Hello</p>"},
                "url-parse": {"url": "https://example.com/path"},
                "markdown-toc": {"markdown": "# Intro\n## Setup"},
                "markdown-links": {"markdown": "[site](https://example.com)"},
                "text-dedupe-lines": {"text": "a\nb\na"},
                "text-sort-lines": {"text": "z\na\nb"},
                "text-case": {"text": "hello WORLD", "mode": "title"},
                "word-frequency": {"text": "red blue red"},
                "html-links": {"html": "<a href='https://example.com'>Example</a>"},
                "json-flatten": {"data": {"a": {"b": 2}}},
                "csv-to-json": {"csv": "name,age\nAda,36\n"},
                "toml-parse": {"toml": "name = 'Plug'"},
                "markdown-table": {"headers": ["name", "score"], "rows": [["Ada", 10]]},
                "markdown-to-text": {"markdown": "# Title\n[site](https://example.com)"},
                "text-wrap": {"text": "one two three four", "width": 10},
                "text-mask-secrets": {"text": "API_KEY=abc123"},
                "regex-replace": {"pattern": "cat", "replacement": "dog", "text": "cat cat"},
                "html-clean": {"html": "<p>Hello <b>world</b></p><script>bad()</script>"},
                "json-merge": {"left": {"a": 1}, "right": {"b": 2}},
                "json-pointer": {"data": {"user": {"name": "Ada"}}, "pointer": "/user/name"},
                "csv-column-select": {"csv": "a,b\n1,2\n", "columns": "b"},
                "csv-sort": {"csv": "name\nZed\nAda\n", "column": "name"},
                "csv-dedupe": {"csv": "id\n1\n1\n2\n"},
                "ini-parse": {"ini": "[app]\nname=Plug"},
                "color-contrast": {"foreground": "#000000", "background": "#FFFFFF"},
                "web-fetch": {"url": "https://example.com"},
                "url-query-parse": {"url": "https://example.com/?a=1&b=2"},
                "text-reverse": {"text": "Plug"},
                "text-sentence-count": {"text": "One. Two! Three?"},
                "text-char-frequency": {"text": "banana"},
                "text-remove-blank": {"text": "one\n\ntwo"},
                "text-indent": {"text": "one\ntwo", "prefix": "  "},
                "text-dedent": {"text": "  one\n  two"},
                "text-number-lines": {"text": "one\ntwo"},
                "text-truncate": {"text": "abcdef", "max_chars": 3},
                "text-prefix-lines": {"text": "one\ntwo", "prefix": "> "},
                "text-suffix-lines": {"text": "one\ntwo", "suffix": ";"},
                "text-unique-words": {"text": "red blue red"},
                "text-palindrome": {"text": "Never odd or even"},
                "text-rot13": {"text": "hello"},
                "json-keys": {"data": {"a": 1, "b": 2}},
                "json-values": {"data": {"a": 1, "b": 2}},
                "json-types": {"data": {"a": 1, "b": "x"}},
                "json-array-stats": {"items": [1, "a", None]},
                "json-sort-keys": {"data": {"z": 1, "a": 2}},
                "json-minify": {"data": {"ok": True}},
                "csv-column-stats": {"csv": "name,age\nAda,36\n", "column": "name"},
                "csv-head": {"csv": "name\nAda\nBob\n", "count": 1},
                "csv-tail": {"csv": "name\nAda\nBob\n", "count": 1},
                "csv-transpose": {"csv": "a,b\n1,2\n"},
                "number-stats": {"values": [1, 2, 3]},
                "number-percentile": {"values": [1, 2, 3, 4], "percentile": 75},
                "json-escape-string": {"text": "hello"},
                "json-unescape-string": {"json_string": "\"hello\""},
                "json-array-filter": {"items": [{"x": 1}, {"x": 2}], "key": "x", "equals": 2},
                "json-array-project": {"items": [{"a": 1, "b": 2}], "fields": ["b"]},
                "json-diff": {"before": {"a": 1}, "after": {"a": 2}},
                "csv-to-markdown": {"csv": "a,b\n1,2\n"},
                "csv-merge": {"first": "a\n1\n", "second": "a\n2\n"},
                "csv-unique-count": {"csv": "x\na\nb\na\n", "column": "x"},
                "csv-sample": {"csv": "x\n1\n2\n3\n", "count": 2},
                "number-standard-deviation": {"values": [1, 2, 3]},
                "number-mode": {"values": [1, 2, 2, 3]},
                "number-round": {"value": 3.14159, "places": 2},
                "number-clamp": {"value": 5, "minimum": 0, "maximum": 3},
                "number-factorial": {"value": 5},
                "number-prime": {"value": 17},
                "number-range": {"start": 1, "stop": 5},
                "number-base-convert": {"value": 255, "base": 16},
                "percentage-calc": {"value": 200, "percent": 15},
                "unit-convert": {"value": 1, "from": "km", "to": "m"},
                "color-hex-rgb": {"hex": "#FF8800"},
                "color-rgb-hex": {"r": 255, "g": 136, "b": 0},
                "ip-cidr-inspect": {"cidr": "192.168.1.0/24"},
                "date-weekday": {"date": "2026-01-01"},
                "date-add-days": {"date": "2026-01-01", "days": 7},
                "date-diff": {"first": "2026-01-01", "second": "2026-01-10"},
                "text-extract-emails": {"text": "mail a@example.com"},
                "text-extract-urls": {"text": "see https://example.com/page"},
                "text-extract-hashtags": {"text": "hello #Plug #AI"},
                "text-extract-mentions": {"text": "hello @bisma"},
                "text-extract-phones": {"text": "call +1 555 123 4567"},
                "text-find-replace": {"text": "cat cat", "find": "cat", "replace": "dog"},
                "text-nonempty-lines": {"text": "a\n\n b"},
                "text-common-prefix": {"left": "prefix-a", "right": "prefix-b"},
                "text-common-suffix": {"left": "a-tail", "right": "b-tail"},
                "text-word-count": {"text": "one two three"},
                "text-paragraph-count": {"text": "one\n\ntwo"},
                "text-title-case": {"text": "hello world"},
                "text-similarity": {"left": "kitten", "right": "sitting"},
                "text-quote-csv": {"text": "a,b"},
                "markdown-checklist": {"markdown": "- [x] Done\n- [ ] Todo"},
                "markdown-frontmatter": {"markdown": "---\ntitle: Hello\n---\nBody"},
                "markdown-heading-levels": {"markdown": "# One\n## Two"},
                "json-deep-count": {"data": {"a": [1, {"b": 2}]}},
                "json-array-sort": {"items": [{"n": 2}, {"n": 1}], "key": "n"},
                "json-array-dedupe": {"items": [1, 1, 2]},
                "csv-column-rename": {"csv": "a,b\n1,2\n", "old": "a", "new": "x"},
                "csv-filter-contains": {"csv": "name\nAda\nBob\n", "column": "name", "contains": "ad"},
                "csv-filter-range": {"csv": "v\n1\n5\n9\n", "column": "v", "minimum": 2, "maximum": 8},
                "csv-pivot": {"csv": "team,score\nA,2\nA,3\nB,4\n", "group_by": "team", "value_column": "score", "aggregate": "sum"},
                "csv-validate": {"csv": "a,b\n1,\n", "required": ["a", "b"]},
                "python-ast-summary": {"source": "import os\ndef f():\n return 1"},
                "python-imports": {"source": "import os\nfrom pathlib import Path"},
                "python-functions": {"source": "def run():\n pass"},
                "python-classes": {"source": "class A:\n def f(self): pass"},
                "lua-functions": {"source": "function hello() end"},
                "lua-requires": {"source": "local x = require(\"ReplicatedStorage.X\")"},
                "js-imports": {"source": "import React from \"react\"; const fs = require(\"fs\");"},
                "js-functions": {"source": "function hello() {} const go = () => 1;"},
                "html-meta-extract": {"html": "<title>Hi</title><meta name=\"description\" content=\"Page\">"},
                "xml-format": {"xml": "<root><x>1</x></root>"},
                "log-level-count": {"text": "INFO start\nERROR fail\nINFO done"},
                "traceback-summary": {"traceback": "File \"a.py\", line 2\nValueError: bad"},
                "git-diff-stats": {"diff": "--- a\n+++ b\n-old\n+new\n"},
                "semver-normalize": {"version": "v01.2.3"},
                "semver-sort": {"versions": ["1.2.0", "1.10.0", "1.3.0"]},
                "duration-parse": {"value": "01:02:03"},
                "image-dimensions": {"path": image_path},
                "file-checksum": {"path": __file__},
                "directory-size": {"path": archive_dir},
                "file-size-human": {"path": __file__},
                "file-mime-guess": {"filename": "photo.png"},
                "file-name-sanitize": {"name": "hello world?.png"},
                "path-extension": {"path": "assets/logo.PNG"},
                "code-fence-extract": {"markdown": "```python\nprint(1)\n```"},
                "markdown-word-count": {"markdown": "# Title\nhello world"},
            }

            class Context:
                def __init__(self, plugin_id):
                    self.plugin_id = plugin_id

                def require(self, permission):
                    return None

            with patch("plug.builtin_catalog._web_fetch", return_value={"status": 200, "text": "ok"}):
                for plugin_id, *_ in PLUGIN_DEFINITIONS:
                    with self.subTest(plugin=plugin_id):
                        result = run_builtin(Context(plugin_id), samples[plugin_id])
                        self.assertIsNotNone(result)

    def test_registry_executes_plugins_and_enforces_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            plugin_root = Path(temp) / "plugins"
            skill_root = Path(temp) / "skills"
            install_builtin_catalog(plugin_root, skill_root)
            registry = PluginRegistry()
            registry.discover(plugin_root)
            registry.enable("math-calc")
            result = asyncio.run(registry.execute("math-calc", arguments={"expression": "6 * 7"}))
            self.assertTrue(result.ok)
            self.assertEqual(result.data["result"], 42)
            registry.enable("files-read")
            with self.assertRaises(PermissionError):
                asyncio.run(registry.execute("files-read", arguments={"path": __file__}))
            result = asyncio.run(registry.execute(
                "files-read", granted_permissions={"filesystem.read"},
                arguments={"path": __file__}))
            self.assertTrue(result.ok)
            registry.enable("web-fetch")
            with self.assertRaises(PermissionError):
                asyncio.run(registry.execute("web-fetch", arguments={"url": "https://example.com"}))
            with patch("plug.builtin_catalog._web_fetch", return_value={"status": 200, "text": "fixture"}):
                granted = asyncio.run(registry.execute("web-fetch", granted_permissions={"network.read"}, arguments={"url": "https://example.com"}))
            self.assertTrue(granted.ok)

    def test_web_fetch_blocks_private_addresses(self):
        from plug.builtin_catalog import _web_fetch

        class Context:
            def require(self, permission):
                self.permission = permission

        context = Context()
        with self.assertRaises(ValueError):
            _web_fetch({"url": "http://127.0.0.1/"}, context)
        self.assertEqual(context.permission, "network.read")

    def test_safe_calculator_rejects_code_execution(self):
        with self.assertRaises((ValueError, SyntaxError)):
            run_builtin(
                SimpleNamespace(plugin_id="math-calc"),
                {"expression": "__import__('os').system('echo unsafe')"},
            )

    def test_checked_in_catalogs_are_discoverable_and_default_install_is_safe(self):
        root = Path(__file__).resolve().parents[1]
        plugins = PluginRegistry()
        skills = SkillRegistry()
        self.assertEqual(len(plugins.discover(root / "plug" / "plugins" / "catalog")), 175)
        self.assertEqual(len(skills.discover(root / "plug" / "skills" / "catalog")), 175)
        result = install_builtin_catalog()
        self.assertTrue(result["already_installed"])
        self.assertEqual(result["plugins"], 175)
        self.assertEqual(result["skills"], 175)

    def test_installer_refuses_to_overwrite_existing_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugins, skills = root / "plugins", root / "skills"
            install_builtin_catalog(plugins, skills)
            with self.assertRaises(FileExistsError):
                install_builtin_catalog(plugins, skills)


if __name__ == "__main__":
    unittest.main()
