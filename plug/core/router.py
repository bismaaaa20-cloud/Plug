"""Fast multi-selection router and workflow arranger for Plug.

Uses cached inverted token indexes to shortlist candidates before scoring.
It recommends and orders tools; it never enables, authorizes, or executes them.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from plug.plugins.manifest import PluginManifest
from plug.skills.loader import Skill, SkillRegistry

_WORD = re.compile(r"[a-z0-9_+-]+", re.IGNORECASE)
_STOP = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "buat", "by", "can", "dengan",
    "di", "do", "for", "from", "i", "in", "is", "it", "ke", "make", "me",
    "my", "of", "on", "or", "please", "saya", "the", "this", "to", "tolong",
    "untuk", "use", "want", "with", "yang",
})

# Broad workflow phases; these are ordering hints, not hard execution rules.
_PHASE_TERMS = (
    ("understand", frozenset({"plan", "planning", "parse", "requirements", "intent", "scope"})),
    ("research", frozenset({"search", "research", "crawl", "scrape", "browse", "web", "source", "collect"})),
    ("analyze", frozenset({"analyze", "analysis", "inspect", "evaluate", "compare", "classify", "extract", "data"})),
    ("create", frozenset({"generate", "create", "write", "draft", "design", "image", "video", "audio", "code", "build"})),
    ("transform", frozenset({"edit", "convert", "transcode", "format", "render", "process", "optimize"})),
    ("validate", frozenset({"test", "validate", "verify", "check", "review", "audit", "proofread"})),
    ("deliver", frozenset({"publish", "upload", "send", "deploy", "export", "share", "post"})),
)
_PHASE_ORDER = {name: index for index, (name, _) in enumerate(_PHASE_TERMS)}


def _tokens(value: str) -> frozenset[str]:
    return frozenset(token.lower() for token in _WORD.findall(value) if token.lower() not in _STOP)


def _index_documents(documents: list[tuple[str, frozenset[str]]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for item_id, terms in documents:
        for term in terms:
            index[term].add(item_id)
    return dict(index)


def _phase_for(terms: frozenset[str]) -> str:
    for phase, phase_terms in _PHASE_TERMS:
        if terms & phase_terms:
            return phase
    return "other"


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    kind: str
    item_id: str
    phase: str
    score: float


@dataclass(frozen=True, slots=True)
class RouteDecision:
    skills: tuple[tuple[Skill, float], ...]
    plugins: tuple[tuple[PluginManifest, float], ...]
    query: str = ""
    active_skill: str | None = None
    workflow: tuple[WorkflowStep, ...] = ()

    @property
    def selected_skill(self) -> Skill | None:
        return self.skills[0][0] if self.skills else None

    @property
    def selected_plugin(self) -> PluginManifest | None:
        return self.plugins[0][0] if self.plugins else None

    @property
    def selected_skills(self) -> tuple[Skill, ...]:
        return tuple(skill for skill, _ in self.skills)

    @property
    def selected_plugins(self) -> tuple[PluginManifest, ...]:
        return tuple(plugin for plugin, _ in self.plugins)


class ContextRouter:
    """Selects many relevant extensions with cached inverted-index retrieval."""

    def __init__(self, skills: SkillRegistry) -> None:
        self.skills = skills
        self._skill_signature: tuple[tuple[str, str, tuple[str, ...]], ...] = ()
        self._skill_index: dict[str, set[str]] = {}
        self._plugin_cache_key: tuple[PluginManifest, ...] | None = None
        self._plugin_index: dict[str, set[str]] = {}
        self._plugin_by_id: dict[str, PluginManifest] = {}

    def _refresh_skill_index(self) -> None:
        skills = tuple(self.skills._skills.values())
        signature = tuple((s.name, s.description, s.triggers) for s in skills)
        if signature == self._skill_signature:
            return
        docs = []
        for skill in skills:
            terms = _tokens(" ".join((skill.name.replace("-", " "), skill.description, *skill.triggers)))
            docs.append((skill.name, terms))
        self._skill_index = _index_documents(docs)
        self._skill_signature = signature

    def _refresh_plugin_index(self, plugins: tuple[PluginManifest, ...]) -> None:
        if plugins == self._plugin_cache_key:
            return
        docs = []
        self._plugin_by_id = {plugin.id: plugin for plugin in plugins}
        for plugin in plugins:
            terms = _tokens(" ".join((
                plugin.name, plugin.description, *plugin.keywords, *plugin.capabilities,
            )))
            docs.append((plugin.id, terms))
        self._plugin_index = _index_documents(docs)
        self._plugin_cache_key = plugins

    @staticmethod
    def _score(query_terms: frozenset[str], doc_terms: frozenset[str], *,
               exact_query: str, phrases: tuple[str, ...], multiplier: float) -> float:
        overlap = len(query_terms & doc_terms)
        if not overlap:
            return 0.0
        # Coverage helps short, highly specific descriptions; overlap rewards
        # documents that match several distinct parts of a complex request.
        coverage = overlap / max(1, len(doc_terms))
        score = overlap + min(coverage, 1.0) * 1.5
        if any(p and p in exact_query for p in phrases):
            score += 2.5
        return score * multiplier

    def route(
        self,
        message: str,
        plugins: Iterable[PluginManifest] = (),
        *,
        limit: int | None = 30,
        context: str = "",
        active_skill: str | Skill | None = None,
    ) -> RouteDecision:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
            raise ValueError("limit must be None or a positive integer")
        if not isinstance(context, str):
            raise TypeError("context must be a string")
        skill_name = active_skill.name if isinstance(active_skill, Skill) else active_skill
        if skill_name is not None and not isinstance(skill_name, str):
            raise TypeError("active_skill must be a skill name or Skill")

        plugin_list = tuple(plugins)
        self._refresh_skill_index()
        self._refresh_plugin_index(plugin_list)

        query = " ".join(part for part in (message, context, skill_name or "") if part)
        query_terms = _tokens(query)
        message_terms = _tokens(message)
        if not query_terms:
            return RouteDecision((), (), query, skill_name, ())

        # Inverted index: only inspect documents sharing at least one query term.
        skill_ids: set[str] = set()
        for term in query_terms:
            skill_ids.update(self._skill_index.get(term, ()))
        plugin_ids: set[str] = set()
        for term in query_terms:
            plugin_ids.update(self._plugin_index.get(term, ()))

        skill_by_name = self.skills._skills
        skill_matches: list[tuple[Skill, float]] = []
        for name in skill_ids:
            skill = skill_by_name[name]
            terms = _tokens(" ".join((skill.name.replace("-", " "), skill.description, *skill.triggers)))
            score = self._score(query_terms, terms, exact_query=query.lower(),
                                phrases=skill.triggers, multiplier=1.0)
            if message_terms:
                score += 0.35 * len(message_terms & terms)
            if skill_name and skill.name == skill_name:
                score += 8.0
            if score > 0:
                skill_matches.append((skill, round(score, 4)))
        skill_matches.sort(key=lambda item: (-item[1], item[0].name))

        plugin_matches: list[tuple[PluginManifest, float]] = []
        for plugin_id in plugin_ids:
            plugin = self._plugin_by_id[plugin_id]
            terms = _tokens(" ".join((
                plugin.name, plugin.description, *plugin.keywords, *plugin.capabilities,
            )))
            phrases = (*plugin.keywords, *plugin.capabilities)
            score = self._score(query_terms, terms, exact_query=query.lower(),
                                phrases=phrases, multiplier=1.0)
            if message_terms:
                score += 0.35 * len(message_terms & terms)
            if skill_name:
                skill_terms = _tokens(skill_name.replace("-", " "))
                score += 0.5 * len(skill_terms & terms)
            if score > 0:
                plugin_matches.append((plugin, round(score, 4)))
        plugin_matches.sort(key=lambda item: (-item[1], item[0].id))

        if limit is not None:
            skill_matches = skill_matches[:limit]
            plugin_matches = plugin_matches[:limit]

        # Combine the chosen skills and plugins into a suggested phase order.
        # Same-phase items are sorted by relevance, then stable ID.
        workflow_items: list[WorkflowStep] = []
        for skill, score in skill_matches:
            terms = _tokens(" ".join((skill.name.replace("-", " "), skill.description, *skill.triggers)))
            workflow_items.append(WorkflowStep("skill", skill.name, _phase_for(terms), score))
        for plugin, score in plugin_matches:
            terms = _tokens(" ".join((plugin.name, plugin.description, *plugin.keywords, *plugin.capabilities)))
            workflow_items.append(WorkflowStep("plugin", plugin.id, _phase_for(terms), score))
        workflow_items.sort(key=lambda step: (
            _PHASE_ORDER.get(step.phase, len(_PHASE_ORDER)), -step.score, step.kind, step.item_id,
        ))

        return RouteDecision(
            tuple(skill_matches), tuple(plugin_matches), query, skill_name, tuple(workflow_items),
        )
