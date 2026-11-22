# Plug — compact repository

Plug is a provider-neutral multi-AI orchestration foundation for Python 3.11+.
The complete project source, tests, docs, 200 built-in plugins, and 200 skills
are preserved in `plug-source.tar.xz`.

## Restore the full source tree

```bash
python install.py --dest ./plug-source
cd plug-source
python -X dev -W error -m unittest discover -s tests -v
```

To restore directly into the current directory, use
`python install.py --dest . --force`.

GitHub Actions verifies the archive, checks the 200-plugin/200-skill catalog,
and enforces a maximum 204,800-byte total for the tracked working tree before
committing the compact form. The original source files are archived, not
discarded.

## Standalone Claude Token Optimizer

This branch also ships `claude-token-optimizer.zip`, a standalone Claude Code
plugin with a local MCP compressor, reversible context vault, conservative
message pruning, coding-efficiency skill, optional Anthropic token counting,
and tests. The ZIP is **13,678 bytes** (limit: 204,800 bytes).

Extract the ZIP, then run `claude --plugin-dir ./claude-token-optimizer` from
the directory containing the extracted plugin folder. See the plugin's README
for setup, tools, and safety details.

## Scope

Plug provides local task planning, routing, teamwork, plugin and skill
registries, and SQLite memory foundations. Real provider/API adapters and
automatic control of external AI applications are not claimed as implemented.
