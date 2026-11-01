"""Deterministic planner; model-generated planning is intentionally out of scope."""

from plug.core.models import Plan, Task


class TaskPlanner:
    """Build a validated plan from explicit task specifications."""

    def build(self, tasks: list[Task] | tuple[Task, ...]) -> Plan:
        return Plan(tuple(tasks))
