import unittest

from plug.core.teamwork import (
    AgentProfile, FriendlyGuide, TaskAllocator, TeamStrategy,
    StrategyEngine, WorkItem, WorkStyle,
)


class TeamworkTests(unittest.TestCase):
    def setUp(self):
        self.agents = (
            AgentProfile("writer", frozenset({"writing", "research"}), reliability=0.9),
            AgentProfile("coder", frozenset({"coding", "testing"}), reliability=0.95),
        )

    def test_allocator_prefers_matching_skills(self):
        work = [WorkItem("code", "Implement feature", frozenset({"coding"}))]
        result = TaskAllocator().allocate(work, self.agents)
        self.assertEqual(result[0].agent_id, "coder")

    def test_allocator_is_deterministic(self):
        work = [WorkItem("a", "Research", frozenset({"research"})),
                WorkItem("b", "Code", frozenset({"coding"}))]
        allocator = TaskAllocator()
        self.assertEqual(allocator.allocate(work, self.agents),
                         allocator.allocate(work, self.agents))

    def test_dependency_order_is_respected(self):
        work = [WorkItem("second", "Review", dependencies=("first",)),
                WorkItem("first", "Draft")]
        result = TaskAllocator().allocate(work, self.agents)
        self.assertEqual([x.work_id for x in result], ["first", "second"])

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):
            TaskAllocator().allocate(
                [WorkItem("x", "Do it", dependencies=("missing",))], self.agents
            )

    def test_cycle_rejected(self):
        work = [WorkItem("a", "A", dependencies=("b",)),
                WorkItem("b", "B", dependencies=("a",))]
        with self.assertRaises(Exception):
            TaskAllocator().allocate(work, self.agents)

    def test_parallel_strategy_for_independent_work(self):
        result = StrategyEngine().choose(
            [WorkItem("a", "A"), WorkItem("b", "B")], 2
        )
        self.assertEqual(result.style, WorkStyle.PARALLEL)

    def test_pipeline_strategy_for_dependencies(self):
        result = StrategyEngine().choose(
            [WorkItem("a", "A"), WorkItem("b", "B", dependencies=("a",))], 2
        )
        self.assertEqual(result.style, WorkStyle.PIPELINE)

    def test_high_risk_work_requires_review(self):
        result = StrategyEngine().choose([WorkItem("a", "A", complexity=5)], 1)
        self.assertTrue(result.review_required)
        self.assertEqual(result.style, WorkStyle.DIRECT)

    def test_empty_plan_is_friendly(self):
        strategy = StrategyEngine().choose([], 1)
        self.assertIn("Belum ada tugas", strategy.rationale)

    def test_friendly_messages_are_constructive(self):
        message = FriendlyGuide.retry("draft", "jelaskan sumber data")
        self.assertIn("Terima kasih", message)
        self.assertIn("penyempurnaan", message)


if __name__ == "__main__":
    unittest.main()
