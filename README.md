# Plug

Plug is a provider-neutral foundation for coordinating a team of AI agents.

## Current scope

- Validated task plans represented as a dependency DAG.
- Parallel execution for independent tasks, with bounded concurrency.
- Sequential execution across dependency layers.
- Explicit agent registry and provider protocol.
- Adaptive task allocation using skill match, reliability, preference, and load.
- Strategy selection: direct, parallel, pipeline, or collaborative.
- Friendly, constructive status and revision messages.
- No mandatory API keys or third-party runtime dependencies for the core.

## Desktop-first direction

Plug is being designed to coordinate AI tools available on the user's computer.
The teamwork algorithm is transport-neutral: future adapters may connect to
local models, desktop applications, or browser sessions where supported.
This repository does not yet claim automatic control of desktop apps or browser
interfaces; that requires a real, tested desktop integration layer.

## Not implemented yet

There is no LLM-driven planner, desktop automation adapter, persistent job
queue, web UI, or automatic model discovery in this stage. Tests use local fake
agents; no provider output is fabricated by the runtime.

## Quick start

Python 3.11+:

```bash
python -m unittest discover -s tests -v
```

No API key is needed to use the planning and allocation core. Any future
integration must document its connection method and permissions explicitly.

## Built-in catalog (35 plugins + 35 skills)

The repository now contains 35 local plugin packages under
`plug/plugins/catalog/` and 35 skill packages under
`plug/skills/catalog/`. Each plugin has a manifest and executable entrypoint;
each skill has a `SKILL.md` and helper script. See
[Built-in catalog documentation](docs/BUILTIN-CATALOG.md).

Install/verify the bundled catalog with:

```bash
python -m plug.builtin_catalog --install
python -m unittest tests.test_builtin_catalog -v
```

## Local extensions (initial foundation)

Plug now includes a local plugin SDK and registry, a portable `SKILL.md` loader,
scaffold builders for both extensions, deterministic context-based selection,
and a local SQLite memory store. See [Plugins and Skills](docs/PLUGINS-AND-SKILLS.md)
for formats, usage boundaries, and current limitations.

Plugin code is trusted Python executed in-process, not sandboxed. Plugins are
disabled by default and require explicit permission grants. Skill helper scripts
are scaffolds and must be reviewed before execution. The current router uses
keyword overlap; it is not yet an LLM-based semantic router. The 100-plugin and
100-skill catalog is a target, not a claim that 200 live integrations are already
implemented.
