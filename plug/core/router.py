"""Deterministic context router for choosing relevant skills and plugins."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from plug.skills.loader import Skill, SkillRegistry
from plug.plugins.manifest import PluginManifest

_WORD = re.compile(r"[a-z0-9_+-]+", re.IGNORECASE)


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in _WORD.findall(value)}


@dataclass(frozen=True, slots=True)
class RouteDecision:
    skills: tuple[tuple[Skill, float], ...]
    plugins: tuple[tuple[PluginManifest, float], ...]


class ContextRouter:
    def __init__(self, skills: SkillRegistry) -> None:
        self.skills = skills

    def route(self, message: str, plugins: Iterable[PluginManifest] = (), *, limit: int = 5) -> RouteDecision:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        if limit < 1:
            raise ValueError("limit must be positive")
        words = _tokens(message)
        skill_matches = self.skills.select(message, limit=limit)
        plugin_matches: list[tuple[PluginManifest, float]] = []
        for plugin in plugins:
            terms = _tokens(" ".join((plugin.name, plugin.description, *plugin.keywords, *plugin.capabilities)))
            score = float(len(words & terms))
            if score:
                plugin_matches.append((plugin, score))
        plugin_matches.sort(key=lambda item: (-item[1], item[0].id))
        return RouteDecision(skill_matches, tuple(plugin_matches[:limit]))
