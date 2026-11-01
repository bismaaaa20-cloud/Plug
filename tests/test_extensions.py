from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from plug.core.router import ContextRouter
from plug.memory.store import MemoryStore
from plug.plugins.builder import create_plugin
from plug.plugins.registry import PluginRegistry
from plug.skills.builder import create_skill
from plug.skills.loader import SkillRegistry


class ExtensionTests(unittest.IsolatedAsyncioTestCase):
    async def test_plugin_builder_discovery_enable_and_execute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_plugin(root, "sample-plugin", name="Sample", description="sample tool")
            registry = PluginRegistry()
            self.assertEqual(registry.discover(root), ("sample-plugin",))
            with self.assertRaises(PermissionError):
                await registry.execute("sample-plugin")
            registry.enable("sample-plugin")
            result = await registry.execute("sample-plugin", arguments={"value": 7})
            self.assertTrue(result.ok)
            self.assertEqual(result.data["received"]["value"], 7)

    def test_skill_builder_discovery_and_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_skill(directory, "python-debugging", description="Debug Python code and trace errors", triggers=("debug python", "traceback"))
            registry = SkillRegistry()
            self.assertEqual(registry.discover(directory), ("python-debugging",))
            selected = registry.select("Please debug this Python traceback")
            self.assertEqual(selected[0][0].name, "python-debugging")
            self.assertIn("Instructions", selected[0][0].instructions)

    def test_context_router_selects_matching_plugin_and_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_skill(directory, "web-research", description="Search and research information on the web", triggers=("web search", "research"))
            skills = SkillRegistry()
            skills.discover(directory)
            plugins = PluginRegistry()
            plugin_root = Path(directory) / "plugins"
            plugin_root.mkdir()
            create_plugin(plugin_root, "web-search", name="Web Search", description="Search the web", keywords=("search", "web"))
            plugins.discover(plugin_root)
            decision = ContextRouter(skills).route("research and search the web", (plugins.get("web-search"),))
            self.assertEqual(decision.skills[0][0].name, "web-research")
            self.assertEqual(decision.plugins[0][0].id, "web-search")

    def test_memory_persists_and_retrieves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.sqlite3"
            store = MemoryStore(path)
            record = store.remember("Plug uses Python and a local SQLite memory engine", category="project")
            reopened = MemoryStore(path)
            results = reopened.search("SQLite Python project")
            self.assertEqual(results[0].id, record.id)
            self.assertTrue(reopened.delete(record.id))
            self.assertEqual(reopened.search("SQLite Python"), ())

    def test_builder_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_skill(directory, "safe-skill", description="A safe skill")
            with self.assertRaises(FileExistsError):
                create_skill(directory, "safe-skill", description="Overwrite")


if __name__ == "__main__":
    unittest.main()
