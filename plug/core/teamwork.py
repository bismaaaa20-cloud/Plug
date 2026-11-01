"""Adaptive task allocation, strategy selection, and friendly team communication.

This module is deliberately interface-neutral: agents may later be backed by
local models, desktop applications, browser sessions, or other adapters.
It does not require API keys or assume that an agent is reachable by HTTP.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from plug.errors import PlanValidationError


class WorkStyle(str, Enum):
    DIRECT = "direct"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    COLLABORATIVE = "collaborative"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class AgentProfile:
    id: str
    skills: frozenset[str] = frozenset()
    capacity: int = 1
    reliability: float = 0.8
    preferred_tasks: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("agent id must not be empty")
        if isinstance(self.capacity, bool) or self.capacity < 1:
            raise ValueError("capacity must be at least 1")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class WorkItem:
    id: str
    description: str
    required_skills: frozenset[str] = frozenset()
    complexity: int = 3
    priority: int = 3
    dependencies: tuple[str, ...] = ()
    category: str = "general"

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.description.strip():
            raise ValueError("work item id and description must not be empty")
        if not 1 <= self.complexity <= 5:
            raise ValueError("complexity must be between 1 and 5")
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be between 1 and 5")
        if self.id in self.dependencies or len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("dependencies must be unique and cannot include the task itself")


@dataclass(frozen=True, slots=True)
class Assignment:
    work_id: str
    agent_id: str
    score: float
    reason: str


@dataclass(frozen=True, slots=True)
class TeamStrategy:
    style: WorkStyle
    rationale: str
    review_required: bool
    parallelism: int


class TaskAllocator:
    """Greedy capability-aware allocator with load and reliability balancing."""

    def allocate(
        self, work: Iterable[WorkItem], agents: Iterable[AgentProfile]
    ) -> tuple[Assignment, ...]:
        items, people = tuple(work), tuple(agents)
        if not people and items:
            raise ValueError("at least one agent is required")
        known = {item.id for item in items}
        if len(known) != len(items):
            raise PlanValidationError("work item IDs must be unique")
        for item in items:
            missing = set(item.dependencies) - known
            if missing:
                raise PlanValidationError(f"unknown dependencies for {item.id}: {sorted(missing)}")

        remaining = {item.id: item for item in items}
        completed: set[str] = set()
        loads = {agent.id: 0 for agent in people}
        assignments: list[Assignment] = []
        while remaining:
            ready = [item for item in items if item.id in remaining and set(item.dependencies) <= completed]
            if not ready:
                raise PlanValidationError("work dependency graph contains a cycle")
            # Prioritize urgent and complex work; keep original order as stable tie-breaker.
            ready.sort(key=lambda item: (-item.priority, -item.complexity, items.index(item)))
            for item in ready:
                eligible = [agent for agent in people if loads[agent.id] < agent.capacity]
                if not eligible:
                    # Capacity is a concurrency hint, not a hard limit for a static plan.
                    eligible = list(people)
                scored = []
                for agent in eligible:
                    overlap = len(item.required_skills & agent.skills)
                    skill_fit = overlap / max(1, len(item.required_skills))
                    preference = 1.0 if item.category in agent.preferred_tasks else 0.0
                    load_penalty = loads[agent.id] / max(1, agent.capacity)
                    score = 0.55 * skill_fit + 0.25 * agent.reliability + 0.10 * preference - 0.10 * load_penalty
                    scored.append((score, -loads[agent.id], agent.id, agent))
                score, _, _, chosen = max(scored, key=lambda row: (row[0], row[1], row[2]))
                matched = sorted(item.required_skills & chosen.skills)
                reason = (
                    f"cocok pada keahlian: {', '.join(matched)}"
                    if matched else "pilihan terbaik berdasarkan keandalan dan beban kerja"
                )
                assignments.append(Assignment(item.id, chosen.id, round(score, 4), reason))
                loads[chosen.id] += 1
                completed.add(item.id)
                del remaining[item.id]
        return tuple(assignments)


class StrategyEngine:
    """Select a collaboration pattern from task shape and risk."""

    def choose(self, work: Iterable[WorkItem], agent_count: int) -> TeamStrategy:
        items = tuple(work)
        if not items:
            return TeamStrategy(WorkStyle.DIRECT, "Belum ada tugas untuk dikerjakan.", False, 1)
        if agent_count < 1:
            raise ValueError("agent_count must be positive")
        dependent = any(item.dependencies for item in items)
        independent_count = sum(not item.dependencies for item in items)
        high_risk = any(item.complexity >= 4 or item.priority >= 5 for item in items)
        if len(items) == 1:
            style, rationale = WorkStyle.DIRECT, "Satu tugas dapat dikerjakan langsung oleh agen paling sesuai."
        elif dependent:
            style, rationale = WorkStyle.PIPELINE, "Tugas berurutan mengikuti dependensi; tugas bebas tetap dapat berjalan paralel."
        elif high_risk:
            style, rationale = WorkStyle.COLLABORATIVE, "Tugas penting atau kompleks mendapat pendekatan kolaboratif."
        elif independent_count > 1 and agent_count > 1:
            style, rationale = WorkStyle.PARALLEL, "Tugas independen dibagi agar dapat dikerjakan bersamaan."
        else:
            style, rationale = WorkStyle.DIRECT, "Pekerjaan dibagi sederhana agar koordinasi tetap ringan."
        return TeamStrategy(
            style=style,
            rationale=rationale,
            review_required=high_risk or len(items) >= 3,
            parallelism=max(1, min(agent_count, independent_count or 1)),
        )


class FriendlyGuide:
    """Short, respectful status messages for a calm and helpful experience."""

    @staticmethod
    def kickoff(task_count: int, agent_count: int, strategy: TeamStrategy) -> str:
        return (
            f"Siap! Ada {task_count} tugas dan {agent_count} AI di tim. "
            f"Aku akan memakai strategi {strategy.style.value} supaya pekerjaan tertata. "
            "Kita kerjakan bertahap dan periksa hasilnya bersama."
        )

    @staticmethod
    def assigned(work_id: str, agent_id: str, reason: str) -> str:
        return f"Tugas '{work_id}' diberikan ke {agent_id} karena {reason}. Semangat, tim!"

    @staticmethod
    def retry(work_id: str, feedback: str) -> str:
        return (
            f"Hasil '{work_id}' masih perlu sedikit penyempurnaan. "
            f"Tolong perbaiki bagian ini: {feedback}. Terima kasih!"
        )

    @staticmethod
    def completed(success: int, total: int) -> str:
        return f"Proses selesai: {success} dari {total} tugas berhasil. Terima kasih untuk kerja samanya!"
