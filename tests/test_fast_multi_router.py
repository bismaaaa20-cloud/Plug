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
