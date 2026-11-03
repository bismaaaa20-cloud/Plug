from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from plug.core.router import ContextRouter
from plug.plugins.manifest import PluginManifest
from plug.skills.builder import create_skill
from plug.skills.loader import SkillRegistry


class ContextRouterAdvancedTests(unittest.TestCase):
    def test_active_skill_and_context_influence_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_skill(
                directory, "youtube-creator",
                description="Plan and produce YouTube videos, scripts, titles and thumbnails",
                triggers=("youtube video", "video script", "creator workflow"),
            )
            create_skill(
                directory, "image-designer",
                description="Generate and edit images, illustrations and visual assets",
                triggers=("image generation", "edit image", "visual design"),
            )
            skills = SkillRegistry()
            skills.discover(directory)
            plugins = [
                PluginManifest(
                    id="youtube-tools", name="YouTube Tools", version="1.0.0",
                    description="Research and prepare YouTube video metadata",
                    entrypoint="plugin.py", capabilities=("youtube", "video-metadata"),
                    keywords=("youtube video", "video publishing"),
                ),
                PluginManifest(
                    id="image-tools", name="Image Tools", version="1.0.0",
                    description="Generate images and edit visual assets",
                    entrypoint="plugin.py", capabilities=("image-generation",),
                    keywords=("image generation", "image editing"),
                ),
            ]
            router = ContextRouter(skills)
            decision = router.route(
                "Bantu buat judul dan script video",
                plugins,
                context="Proyek channel YouTube, siapkan workflow creator",
            )
            self.assertEqual(decision.selected_skill.name, "youtube-creator")
            self.assertEqual(decision.selected_plugin.id, "youtube-tools")

    def test_explicit_active_skill_is_a_strong_routing_signal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_skill(directory, "python-debugging",
                         description="Debug Python errors", triggers=("debug python",))
            create_skill(directory, "web-research",
                         description="Research information online", triggers=("web research",))
            skills = SkillRegistry()
            skills.discover(directory)
            decision = ContextRouter(skills).route(
                "help me with this task", active_skill="web-research"
            )
            self.assertEqual(decision.selected_skill.name, "web-research")
            self.assertEqual(decision.active_skill, "web-research")

    def test_rejects_invalid_limit_and_context(self) -> None:
        router = ContextRouter(SkillRegistry())
        with self.assertRaises(ValueError):
            router.route("find a plugin", limit=0)
        with self.assertRaises(TypeError):
            router.route("find a plugin", context={"task": "research"})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
