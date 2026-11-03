# Plug Lean Mode

Plug's lean policy is designed to stay cheap at session start and load detail only when needed.

## Always-on layer

Coding agents that support repository instruction files should load the root `AGENTS.md`.
Keep that file short: it is the standing policy, not a project handbook. Avoid putting
catalogues, examples, long architecture explanations, or historical logs there.

## Working loop

1. Read the request and inspect only the files and callers that can affect the change.
2. Search for an existing implementation before creating a new abstraction or dependency.
3. Prefer a focused edit and batch independent file lookups or checks.
4. Do not reread unchanged files; use targeted ranges for large files.
5. Return the result first. Include only decisions, risks, and validation that matter.
6. Run the narrowest relevant test, then the full suite when practical.
7. Never reduce security, input validation, data-loss handling, privacy, or accessibility
   to save tokens or time.

## Memory: store once, recall selectively

Use the local SQLite `MemoryStore` for durable decisions, constraints, architecture facts,
and unresolved work. Store concise, factual notes rather than full transcripts or raw tool
output. Exact duplicate content/category pairs are ignored.

At task/session start, call `recall_context(task, max_tokens=...)` and inject only the
returned relevant notes. The default budget is 256 estimated tokens and five records.
The estimate is a conservative UTF-8 byte heuristic, not an exact model tokenizer.
Do not load all memories by default. Do not store secrets, credentials, private keys,
or sensitive personal data.

## Skill and plugin loading

Keep router output to compact IDs and phases. Load a selected skill's full instructions
only when the current task actually needs them. Load plugin documentation or schemas
only for the selected plugin and action. Never place all plugin manifests, skill bodies,
or permission lists into every prompt.

## Honest reporting

Distinguish recommendation from execution. State exactly which tests ran and whether they
passed. Do not claim automatic session capture, semantic retrieval, exact token counts,
or sandboxing unless those capabilities are implemented and verified.
