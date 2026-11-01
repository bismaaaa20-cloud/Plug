# Plug

Plug is a provider-neutral foundation for orchestrating multi-AI workflows.

## Current scope

- Explicit task plans represented as a validated dependency DAG.
- Parallel execution for independent tasks, with bounded concurrency.
- Sequential execution across dependency layers.
- Provider protocol and explicit provider registry.
- Environment-backed runtime settings.
- No API keys or third-party runtime dependencies are required for the core.

## Not implemented yet

There is no LLM-driven planner, live provider adapter, persistent job queue,
web UI, or automatic model selection in this stage. Tests use local fake
providers; no provider output is fabricated by the runtime.

## Quick start

Python 3.11+:

```python
import asyncio
from plug import AsyncExecutor, Plan, Task, ProviderRegistry

# Register an implementation of the Provider protocol, then:
# plan = Plan((Task("draft", "Draft an outline", "your-provider"),))
# results = await AsyncExecutor(registry).execute(plan)
```

Run the standard-library tests:

```bash
python -m unittest discover -s tests -v
```

Provider credentials should be supplied through environment variables or a
secret manager by future provider adapters. Never commit secrets.
