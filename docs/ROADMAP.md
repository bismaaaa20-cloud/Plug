# Roadmap

1. Harden domain models and deterministic DAG execution.
2. Add planner strategies and explicit plan-review hooks.
3. Add opt-in provider adapters using official APIs and environment/secret
   manager credentials.
4. Add durable job state, retries, cancellation, and observability.
5. Add human approval gates for expensive or consequential actions.
6. Add integration and compatibility tests across supported Python versions.

No live provider is enabled by default. Users must configure credentials
before any real provider adapter can make network requests.
