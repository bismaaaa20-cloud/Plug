# Plug — compact repository

Plug is a provider-neutral multi-AI orchestration foundation for Python 3.11+.
It includes the runtime, tests, documentation, 200 built-in plugins, and 200
task-specific skills.

## Restore the complete source tree

This repository stores the complete project in `plug-source.zip` to keep the
Git working tree at or below 200 KiB. Restore it with:

```bash
python install.py --dest ./plug-source
cd plug-source
python -X dev -W error -m unittest discover -s tests -v
```

To restore directly into the current directory, use
`python install.py --dest . --force`.

The compact archive is checked by GitHub Actions before it is committed.
The 200 plugin manifests, 200 skill definitions, runtime modules, tests, and
documentation remain inside the archive; they are not discarded.

## Scope and limitations

The project provides local planning, task routing, teamwork, plugin and skill
registries, and SQLite memory foundations. Real provider/API adapters and
automatic control of external AI applications are not claimed as implemented.
