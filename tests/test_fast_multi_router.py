from __future__ import annotations

import tempfile
import unittest

from plug.core.router import ContextRouter
from plug.plugins.manifest import PluginManifest
from plug.skills.builder import create_skill
from plug.skills.loader import SkillRegistry


class FastMultiRouterTests(unittest.TestCase):
    def test_selects_hundreds_of_relevant_plugins_without_single_pick_cap(self) -> None:
        plugins = tuple(
            PluginManifest(
                id=f"web-search-{index:03d}",
                name=f"Web Search Connector {index}",
                version="1.0.0",
                description="Search the web and collect research sources",
                entrypoint="plugin.py",
                capabilities=("web-search", "research"),
                keywords=("web search", "research sources"),
            )
            for index in range(300)
        )
        router = ContextRouter(SkillRegistry())
        decision = router.route("research sources and web search", plugins, limit=300)
        self.assertEqual(len(decision.plugins), 300)
        self.assertEqual(len(decision.selected_plugins), 300)

    def test_none_limit_returns_all_relevant_plugins_and_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for index in range(35):
                create_skill(
                    directory,
                    f"research-skill-{index:02d}",
                    description="Research web sources and summarize findings",
                    triggers=("web research", "source analysis"),
                )
            skills = SkillRegistry()
            skills.discover(directory)
            plugins = tuple(
                PluginManifest(
                    id=f"research-tool-{index:02d}",
                    name=f"Research Tool {index}",
                    version="1.0.0",
                    description="Research web sources and summarize findings",
                    entrypoint="plugin.py",
                    capabilities=("web-research",),
                    keywords=("web research",),
                )
                for index in range(40)
            )
            decision = ContextRouter(skills).route(
                "web research and summarize sources", plugins, limit=None
            )
            self.assertEqual(len(decision.skills), 35)
            self.assertEqual(len(decision.plugins), 40)

    def test_prompt_context_is_compact_and_never_includes_skill_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_skill(
                directory, "deep-research",
                description="Research and summarize sources",
                triggers=("web research",),
            )
            skills = SkillRegistry()
            skills.discover(directory)
            decision = ContextRouter(skills).route("web research sources", (), limit=10)
            compact = decision.to_prompt_context(max_tokens=40)
            self.assertIn("skill:deep-research", compact)
            self.assertNotIn("Research and summarize sources", compact)
            self.assertNotIn("instructions", compact.lower())
            self.assertLessEqual((len(compact.encode("utf-8")) + 2) // 3, 40)

    def test_prompt_context_respects_item_cap_and_validates_budget(self) -> None:
        plugins = tuple(
            PluginManifest(
                id=f"web-search-{index:02d}", name=f"Web Search {index}",
                version="1.0.0", description="Search web sources and research",
                entrypoint="plugin.py", capabilities=("web-search",),
                keywords=("web research",),
            )
            for index in range(8)
        )
        decision = ContextRouter(SkillRegistry()).route(
            "web research search sources", plugins, limit=8
        )
        compact = decision.to_prompt_context(max_tokens=200, max_items=3)
        self.assertLessEqual(compact.count("plugin:"), 3)
        with self.assertRaises(ValueError):
            decision.to_prompt_context(max_tokens=0)

    def test_workflow_orders_research_before_creation_and_delivery(self) -> None:
        plugins = (
            PluginManifest(
                id="publish-video", name="Publish Video", version="1.0.0",
                description="Upload and publish finished video", entrypoint="plugin.py",
                capabilities=("publish", "upload"), keywords=("publish video",),
            ),
            PluginManifest(
                id="make-video", name="Create Video", version="1.0.0",
                description="Generate and render video content", entrypoint="plugin.py",
                capabilities=("video-generation", "render"), keywords=("create video",),
            ),
            PluginManifest(
                id="research-web", name="Web Research", version="1.0.0",
                description="Search web sources and collect research", entrypoint="plugin.py",
                capabilities=("web-search",), keywords=("web research",),
            ),
        )
        decision = ContextRouter(SkillRegistry()).route(
            "research web, create video, and publish video", plugins, limit=10
        )
        phases = [step.phase for step in decision.workflow]
        self.assertEqual(phases, ["research", "create", "deliver"])
        self.assertEqual(decision.workflow[0].item_id, "research-web")


if __name__ == "__main__":
    unittest.main()
