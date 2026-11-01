"""Immutable domain models and DAG validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from plug.errors import PlanValidationError


class TaskStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    prompt: str
    provider: str
    dependencies: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("id", "prompt", "provider"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise PlanValidationError(f"{name} must be a non-empty string")
        deps = tuple(self.dependencies)
        if any(not isinstance(dep, str) or not dep for dep in deps):
            raise PlanValidationError("dependencies must contain non-empty task IDs")
        if len(set(deps)) != len(deps):
            raise PlanValidationError(f"task {self.id!r} has duplicate dependencies")
        if self.id in deps:
            raise PlanValidationError(f"task {self.id!r} cannot depend on itself")
        object.__setattr__(self, "dependencies", deps)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class Plan:
    tasks: tuple[Task, ...]

    def __post_init__(self) -> None:
        tasks = tuple(self.tasks)
        object.__setattr__(self, "tasks", tasks)
        ids = [task.id for task in tasks]
        if len(ids) != len(set(ids)):
            raise PlanValidationError("task IDs must be unique")
        known = set(ids)
        for task in tasks:
            missing = set(task.dependencies) - known
            if missing:
                raise PlanValidationError(
                    f"task {task.id!r} has unknown dependencies: {sorted(missing)}"
                )
        self.layers()  # also detects cycles

    def layers(self) -> tuple[tuple[Task, ...], ...]:
        remaining = {task.id: task for task in self.tasks}
        completed: set[str] = set()
        result: list[tuple[Task, ...]] = []
        while remaining:
            ready = tuple(
                task for task in self.tasks
                if task.id in remaining and set(task.dependencies) <= completed
            )
            if not ready:
                raise PlanValidationError("task dependency graph contains a cycle")
            result.append(ready)
            for task in ready:
                completed.add(task.id)
                del remaining[task.id]
        return tuple(result)


@dataclass(frozen=True, slots=True)
class TaskResult:
    task_id: str
    status: TaskStatus
    output: str | None = None
    error_type: str | None = None
