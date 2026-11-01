from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from plug.plugins.builder import create_plugin
from plug.plugins.manifest import PluginManifest
from plug.plugins.registry import PluginRegistry
from plug.skills.builder import create_skill
from plug.skills.loader import SkillRegistry


class RegistryHardeningTests(unittest.TestCase):
    def test_manifest_rejects_string_instead_of_permission_list(self):
        with self.assertRaisesRegex(ValueError, "permissions must be a list"):
            PluginManifest.from_dict({
                "id": "sample-plugin", "name": "Sample", "version": "1",
                "description": "sample", "permissions": "network.read",
            })

    def test_manifest_rejects_duplicate_permissions(self):
        with self.assertRaisesRegex(ValueError, "must not contain duplicates"):
            PluginManifest.from_dict({
                "id": "sample-plugin", "name": "Sample", "version": "1",
                "description": "sample", "permissions": ["network.read", "network.read"],
            })

    def test_plugin_discovery_is_transactional(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            create_plugin(root, "valid-plugin", name="Valid", description="valid")
            bad = root / "z-broken"
            bad.mkdir()
            (bad / "plugin.json").write_text("{not json", encoding="utf-8")
            registry = PluginRegistry()
            with self.assertRaises(json.JSONDecodeError):
                registry.discover(root)
            self.assertEqual(registry.names(), ())

    def test_plugin_id_must_match_package_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            create_plugin(root, "folder-name", name="Valid", description="valid")
            manifest_path = root / "folder-name" / "plugin.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["id"] = "other-name"
            manifest_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match directory"):
                PluginRegistry().discover(root)

    def test_skill_discovery_is_transactional(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            create_skill(root, "valid-skill", description="valid skill")
            bad = root / "z-broken"
            bad.mkdir()
            (bad / "SKILL.md").write_text("---\nname: broken\ndescription: [bad\n", encoding="utf-8")
            registry = SkillRegistry()
            with self.assertRaises(ValueError):
                registry.discover(root)
            self.assertEqual(registry.names(), ())

    def test_skill_name_must_match_package_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            create_skill(root, "folder-name", description="valid skill")
            skill_file = root / "folder-name" / "SKILL.md"
            skill_file.write_text(
                "---\nname: other-name\ndescription: valid skill\n---\nbody\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "does not match directory"):
                SkillRegistry().discover(root)


if __name__ == "__main__":
    unittest.main()
