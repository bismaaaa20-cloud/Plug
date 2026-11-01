# Architecture

Plug is organized into small layers with explicit contracts:

- `core/models.py` owns immutable task and plan models, including DAG validation.
- `core/planner.py` converts explicit task specifications into plans.
- `core/executor.py` runs dependency layers with bounded async concurrency.
- `providers/` defines the provider protocol and explicit provider registry.
- `plugins/` validates manifests, discovers local packages, checks enablement
  and declared permissions, then calls a plugin entrypoint.
- `skills/` indexes portable `SKILL.md` instructions and ranks likely matches.
- `memory/` stores local structured memory.
- `builtin_catalog.py` defines and installs the first-party catalog.

## Invariants

1. Task IDs, provider names, plugin IDs, and skill names are unique in their
   respective registries.
2. Plans reject missing dependencies and cycles before execution.
3. Plugin and skill discovery is transactional: a failed scan does not leave
   partially registered entries.
4. Plugin and skill package directories must remain directly inside their
   configured catalog roots; package IDs/names must match their directory.
5. Plugins are disabled until explicitly enabled. Declared permissions must
   be granted before execution.
6. Results and errors should avoid retaining raw exception messages, which may
   contain prompts, credentials, or other sensitive values.

## Trust and execution boundary

A permission check is an application-level policy gate, not an operating-system
sandbox. Python plugins execute in the host process with the host user's access.
Only install and enable code that has been reviewed. For untrusted third-party
code, use a separate process/container with OS-level filesystem, network,
resource,
and identity restrictions; that isolation is not implemented by this package.

Skills are instruction documents, not executable plugins. Their optional helper
scripts are not run by the skill loader. A skill can only use capabilities
provided by the agent/runtime that consumes it.

The executor bounds concurrent provider calls, but does not yet provide durable
queues, retries, cancellation policies, distributed scheduling, or process
isolation. Browser automation and video decoding likewise require external
adapters; a catalog entry or skill document does not create those capabilities.
