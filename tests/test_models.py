import unittest
from plug.core.models import Plan, Task, TaskStatus
from plug.errors import PlanValidationError

class ModelTests(unittest.TestCase):
    def test_layers_follow_dependencies(self):
        plan = Plan((Task("a", "A", "p"), Task("b", "B", "p", ("a",))))
        self.assertEqual([[t.id for t in layer] for layer in plan.layers()], [["a"], ["b"]])
    def test_cycle_rejected(self):
        with self.assertRaises(PlanValidationError):
            Plan((Task("a", "A", "p", ("b",)), Task("b", "B", "p", ("a",))))
    def test_missing_dependency_rejected(self):
        with self.assertRaises(PlanValidationError):
            Plan((Task("a", "A", "p", ("missing",)),))
    def test_status_values(self):
        self.assertEqual(TaskStatus.SUCCEEDED.value, "succeeded")
