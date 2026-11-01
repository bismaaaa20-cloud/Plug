# Plugins, Skills, Routing, and Memory

This release adds a first usable local extension foundation to Plug.

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

A skill is a portable directory with a `SKILL.md` file. Its front matter requires `name` and `description`; optional comma-separated `triggers` help deterministic selection. The remaining Markdown is instruction content for an AI provider. Skills are instructions, not automatically executable Python. Optional helper scripts must be reviewed and explicitly invoked by a trusted executor.

Create a scaffold with `plug.skills.builder.create_skill(...)`.

## Context routing

`ContextRouter` ranks skills by trigger and description token overlap and plugins by name, description, keywords, and capabilities. This is a deterministic baseline, not semantic/LLM reasoning. A future model-assisted router can be added behind the same decision interface. A route is a recommendation; it does not execute a plugin or grant permissions.

## Memory

`MemoryStore` stores records in a local SQLite database and performs simple lexical retrieval. It does not automatically ingest every conversation, infer sensitive facts, or sync data to a cloud service. The application must decide what is appropriate to remember and when to retrieve it.

## Current limitations

The repository currently bundles exactly 25 working local plugins and 25 task skills; see [BUILTIN-CATALOG.md](BUILTIN-CATALOG.md) for the complete inventory and tests. These are local tools and instruction packages, not 25 live third-party account integrations. External services still require a real adapter, documented API, credentials, permission review, and integration tests. Catalog entries must not be marked connected until those checks pass. MCP is intentionally not included.
