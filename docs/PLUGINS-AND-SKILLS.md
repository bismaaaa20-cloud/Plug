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

## Automatic context routing

`ContextRouter.route(message, plugins, context="", active_skill=None, limit=5)` ranks the available skills and plugins for the current task.

- Uses the user's current request, optional task context, skill descriptions, skill triggers, plugin names, descriptions, keywords, and declared capabilities.
- Gives stronger weight to exact/multiword trigger and keyword matches than loose token overlap.
- Can use the currently active skill as an additional signal, so the selector can choose companion plugins that fit the skill workflow.
- Returns ranked skill and plugin candidates plus `selected_skill` and `selected_plugin` convenience properties.
- Uses deterministic scoring and stable tie-breaking; it does not call an LLM or require an API key.

Example:

```python
decision = router.route(
    "Prepare a YouTube video script and title",
    available_plugins,
    context="Current project: YouTube creator workflow",
    active_skill="youtube-creator",
)
plugin_candidates = decision.plugins
skill_candidates = decision.skills
```

**Important safety boundary:** routing is recommendation only. It does not enable a plugin, grant permissions, execute tools, or bypass user approval. The caller must filter candidates against enabled state, granted permissions, required credentials, and action-specific approval before execution. The router is more context-aware than simple keyword overlap, but it is still deterministic—not semantic LLM reasoning.

## Memory

`MemoryStore` stores records in a local SQLite database and performs simple lexical retrieval. It does not automatically ingest every conversation, infer sensitive facts, or sync data to a cloud service. The application must decide what is appropriate to remember and when to retrieve it.

## Current limitations

The bundled catalog is documented in [BUILTIN-CATALOG.md](BUILTIN-CATALOG.md). These are local tools and instruction packages, not necessarily live third-party account integrations. External services still require a real adapter, documented API, credentials, permission review, and integration tests. Catalog entries must not be marked connected until those checks pass. MCP is intentionally not included.
