"""Load portable SKILL.md instructions and rank them for a user message."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_WORD = re.compile(r"[a-z0-9_+-]+", re.IGNORECASE)


def _tokens(value: str) -> set[str]:
    return {item.lower() for item in _WORD.findall(value)}


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    description: str
    triggers: tuple[str, ...]
    instructions: str
    path: Path


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    @staticmethod
    def _parse(path: Path) -> Skill:
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            raise ValueError(f"{path} must start with SKILL.md front matter")
        try:
            _, header, body = content.split("---", 2)
        except ValueError as exc:
            raise ValueError(f"{path} has invalid front matter") from exc
        fields: dict[str, str] = {}
        for line in header.strip().splitlines():
            if not line.strip():
                continue
            if ":" not in line:
                raise ValueError(f"invalid front matter line: {line}")
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"\'')
        name, description = fields.get("name", ""), fields.get("description", "")
        if not name or not description:
            raise ValueError("skill front matter requires name and description")
        triggers = tuple(item.strip().lower() for item in fields.get("triggers", "").split(",") if item.strip())
        return Skill(name.lower(), description, triggers, body.strip(), path.parent.resolve())

    def discover(self, root: str | Path) -> tuple[str, ...]:
        base = Path(root)
        if not base.exists():
            return ()
        found: list[str] = []
        for path in sorted(base.glob("*/SKILL.md")):
            skill = self._parse(path)
            if skill.name in self._skills:
                raise ValueError(f"duplicate skill name: {skill.name}")
            self._skills[skill.name] = skill
            found.append(skill.name)
        return tuple(found)

    def get(self, name: str) -> Skill:
        return self._skills[name.lower()]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._skills))

    def select(self, message: str, *, limit: int = 5) -> tuple[tuple[Skill, float], ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        message_tokens = _tokens(message)
        scored: list[tuple[Skill, float]] = []
        for skill in self._skills.values():
            trigger_tokens = set().union(*(_tokens(trigger) for trigger in skill.triggers)) if skill.triggers else set()
            description_tokens = _tokens(skill.description)
            score = 3.0 * len(message_tokens & trigger_tokens) + len(message_tokens & description_tokens)
            if score > 0:
                scored.append((skill, score))
        return tuple(sorted(scored, key=lambda item: (-item[1], item[0].name))[:limit])
