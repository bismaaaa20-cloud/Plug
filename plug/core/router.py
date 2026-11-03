"""Context-aware, explainable selector for Plug skills and plugins.

The router ranks candidates only. It never enables plugins, grants permissions,
or executes tools; callers must enforce those controls separately.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from plug.plugins.manifest import PluginManifest
from plug.skills.loader import Skill, SkillRegistry

_WORD = re.compile(r"[a-z0-9_+-]+", re.IGNORECASE)
_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "buat", "by", "can", "dengan",
    "di", "do", "for", "from", "i", "in", "is", "it", "ke", "make", "me",
    "my", "of", "on", "or", "please", "saya", "the", "this", "to", "tolong",
    "untuk", "use", "want", "with", "yang",
}


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in _WORD.findall(value) if token.lower() not in _STOP}


def _phrase_score(query: str, phrase: str) -> float:
    normalized = " ".join(_WORD.findall(phrase.lower()))
    if not normalized:
        return 0.0
    query_normalized = " ".join(_WORD.findall(query.lower()))
    if normalized in query_normalized:
        return 3.0 + min(len(normalized.split()), 4) * 0.25
    phrase_tokens = _tokens(phrase)
    query_tokens = _tokens(query)
    if not phrase_tokens or not query_tokens:
        return 0.0
    overlap = len(phrase_tokens & query_tokens)
    coverage = overlap / len(phrase_tokens)
    return coverage * (1.5 + min(len(phrase_tokens), 4) * 0.25)


@dataclass(frozen=True, slots=True)
class RouteDecision:
    skills: tuple[tuple[Skill, float], ...]
    plugins: tuple[tuple[PluginManifest, float], ...]
    query: str = ""
    active_skill: str | None = None

    @property
    def selected_skill(self) -> Skill | None:
        return self.skills[0][0] if self.skills else None

    @property
    def selected_plugin(self) -> PluginManifest | None:
        return self.plugins[0][0] if self.plugins else None


class ContextRouter:
    """Ranks relevant skills and plugins using request + task context."""

    def __init__(self, skills: SkillRegistry) -> None:
        self.skills = skills

    def route(
        self,
        message: str,
        plugins: Iterable[PluginManifest] = (),
        *,
        limit: int = 5,
        context: str = "",
        active_skill: str | Skill | None = None,
    ) -> RouteDecision:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if not isinstance(context, str):
            raise TypeError("context must be a string")

        skill_name = active_skill.name if isinstance(active_skill, Skill) else active_skill
        if skill_name is not None and not isinstance(skill_name, str):
            raise TypeError("active_skill must be a skill name or Skill")

        query = " ".join(part for part in (message, context, skill_name or "") if part)
        skill_matches: list[tuple[Skill, float]] = []
        for skill in self.skills._skills.values():
            score = _phrase_score(message, skill.description) * 0.7
            score += sum(_phrase_score(message, trigger) * 1.8 for trigger in skill.triggers)
            if context:
                score += _phrase_score(context, skill.description) * 0.35
                score += sum(_phrase_score(context, trigger) * 0.7 for trigger in skill.triggers)
            if skill_name and skill.name == skill_name:
                score += 5.0
            if score > 0:
                skill_matches.append((skill, round(score, 4)))
        skill_matches.sort(key=lambda item: (-item[1], item[0].name))

        plugin_matches: list[tuple[PluginManifest, float]] = []
        for plugin in plugins:
            score = _phrase_score(message, plugin.name) * 1.2
            score += _phrase_score(message, plugin.description) * 0.8
            score += sum(_phrase_score(message, item) * 1.8 for item in plugin.keywords)
            score += sum(_phrase_score(message, item) * 1.5 for item in plugin.capabilities)
            if context:
                score += _phrase_score(context, plugin.description) * 0.35
                score += sum(_phrase_score(context, item) * 0.6 for item in plugin.capabilities)
            if skill_name:
                score += sum(_phrase_score(skill_name.replace("-", " "), item) * 0.6
                             for item in (*plugin.keywords, *plugin.capabilities))
            if score > 0:
                plugin_matches.append((plugin, round(score, 4)))
        plugin_matches.sort(key=lambda item: (-item[1], item[0].id))

        return RouteDecision(
            tuple(skill_matches[:limit]),
            tuple(plugin_matches[:limit]),
            query=query,
            active_skill=skill_name,
        )
