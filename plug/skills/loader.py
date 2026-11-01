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
    """Read-only skill index with transactional, path-contained discovery."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    @staticmethod
    def _parse(path: Path) -> Skill:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        if not lines or lines[0] != "---":
            raise ValueError(f"{path} must start with SKILL.md front matter")
        try:
            closing = lines.index("---", 1)
        except ValueError as exc:
            raise ValueError(f"{path} has invalid front matter") from exc

        fields: dict[str, str] = {}
        for line in lines[1:closing]:
            if not line.strip():
                continue
            if ":" not in line:
                raise ValueError(f"invalid front matter line: {line}")
            key, value = line.split(":", 1)
            key = key.strip()
            if key not in {"name", "description", "triggers"}:
                raise ValueError(f"unknown skill front matter field: {key}")
            if key in fields:
                raise ValueError(f"duplicate skill front matter field: {key}")
            fields[key] = value.strip().strip('"\\'')
        name, description = fields.get("name", ""), fields.get("description", "")
        if not name or not description:
            raise ValueError("skill front matter requires name and description")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name.lower()):
            raise ValueError("skill name must be lowercase kebab-case")
        triggers = tuple(item.strip().lower() for item in fields.get("triggers", "").split(",") if item.strip())
        instructions = "\n".join(lines[closing + 1:]).strip()
        return Skill(name.lower(), description, triggers, instructions, path.parent.resolve())

    def discover(self, root: str | Path) -> tuple[str, ...]:
        base = Path(root).resolve()
        if not base.exists():
            return ()
        if not base.is_dir():
            raise NotADirectoryError(base)

        pending: dict[str, Skill] = {}
        found: list[str] = []
        for skill_file in sorted(base.glob("*/SKILL.md")):
            package_path = skill_file.parent
            skill_dir = package_path.resolve()
            if package_path.is_symlink() or skill_dir.parent != base:
                raise ValueError(f"skill directory escapes catalog root: {package_path}")
            if skill_file.is_symlink() or not skill_file.is_file():
                raise ValueError(f"invalid skill file path: {skill_file}")
            skill = self._parse(skill_file)
            if skill.name != package_path.name:
                raise ValueError(
                    f"skill name {skill.name!r} does not match directory {package_path.name!r}"
                )
            if skill.name in self._skills or skill.name in pending:
                raise ValueError(f"duplicate skill name: {skill.name}")
            pending[skill.name] = skill
            found.append(skill.name)

        self._skills.update(pending)
        return tuple(found)

    def get(self, name: str) -> Skill:
        return self._skills[name.lower()]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._skills))

    def select(self, message: str, *, limit: int = 5) -> tuple[tuple[Skill, float], ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        message_tokens = _tokens(message)
        scored: list[tuple[Skill, float]] = []
        for skill in self._skills.values():
            trigger_tokens = set().union(*(_tokens(trigger) for trigger in skill.triggers)) if skill.triggers else set()
            description_tokens = _tokens(skill.description)
            score = 3.0 * len(message_tokens & trigger_tokens) + len(message_tokens & description_tokens)
            if score > 0:
                scored.append((skill, score))
        return tuple(sorted(scored, key=lambda item: (-item[1], item[0].name))[:limit])
