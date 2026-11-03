# Plugins, Skills, Routing, and Memory

This release adds a local extension foundation and an explainable context-based selector to Plug.

## Plugins

A plugin is a trusted local Python package directory containing `plugin.json` and an entrypoint such as `plugin.py`. The entrypoint must expose `run(context, arguments)`; synchronous and asynchronous functions are supported. Plugins are discovered but are disabled by default. Enable a plugin explicitly and grant every permission listed in its manifest before execution.

Example manifest:

```json
{
  "id": "example-plugin",
  "name": "Example Plugin",
  "version": "0.1.0",
  "description": "An example local plugin",
  "entrypoint": "plugin.py",
  "capabilities": ["text-processing"],
  "permissions": [],
  "keywords": ["example", "text"]
}
```

Plugins execute as Python code in the Plug process. This is **not a sandbox**. Only install and enable code you trust. Never put API keys in manifests or source files; integrations should read secrets from an approved secret store or environment configuration. Network and filesystem permissions are declarations and must be enforced by the plugin author/integration layer; the current SDK only checks declared permission grants before execution.

Create a scaffold with `plug.plugins.builder.create_plugin(...)`.

## Skills

A skill is a portable directory with a `SKILL.md` file. Its front matter requires `name` and `description`; optional comma-separated `triggers` improve selection. The remaining Markdown is instruction content for an AI provider. Skills are instructions, not automatically executable Python. Optional helper scripts must be reviewed and explicitly invoked by a trusted executor.

Create a scaffold with `plug.skills.builder.create_skill(...)`.

## Automatic multi-plugin and skill routing

`ContextRouter.route(message, plugins, context="", active_skill=None, limit=30)` returns multiple relevant skills and plugins, not just one winner. Set `limit=300` to allow up to 300 of each type, or `limit=None` to return every matching candidate. The default is 30 per type.

The fast selector uses a cached inverted token index:
1. Normalize the request and optional project context once.
2. Retrieve only skill/plugin IDs whose indexed terms overlap the request, rather than rescoring every catalog entry.
3. Score shortlisted candidates using token overlap, coverage, exact trigger/keyword phrase matches, and the active skill signal.
4. Return stable relevance-ranked skill and plugin lists.
5. Build a suggested workflow order by broad phase: understand, research, analyze, create, transform, validate, deliver. Items in the same phase are ordered by relevance and stable ID.

The decision exposes `selected_skills`, `selected_plugins`, and `workflow` in addition to the ranked score tuples. The old singular `selected_skill` and `selected_plugin` convenience properties remain for compatibility.

Example:

```python
decision = router.route(
    "Research this topic, create images and a video, then publish",
    available_plugins,
    context="Current project: YouTube creator workflow",
    active_skill="youtube-creator",
    limit=300,
)
for step in decision.workflow:
    print(step.phase, step.kind, step.item_id)
```

**Important safety and planning boundaries:** this is a fast deterministic candidate selector and phase arranger, not an LLM semantic planner or dependency solver. The phase order is a heuristic suggestion; it does not prove that outputs/inputs match or that every step is required. It never enables a plugin, grants permissions, executes tools, or bypasses user approval. The caller must validate dependencies, enabled state, permissions, credentials, and action-specific approval before execution.

## Memory

`MemoryStore` stores records in a local SQLite database and performs simple lexical retrieval. It does not automatically ingest every conversation, infer sensitive facts, or sync data to a cloud service. The application must decide what is appropriate to remember and when to retrieve it.

## Current limitations

The bundled catalog is documented in [BUILTIN-CATALOG.md](BUILTIN-CATALOG.md). These are local tools and instruction packages, not necessarily live third-party account integrations. External services still require a real adapter, documented API, credentials, permission review, and integration tests. Catalog entries must not be marked connected until those checks pass. MCP is intentionally not included.
