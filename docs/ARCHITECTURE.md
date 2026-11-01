# Architecture

- `Task` describes one unit of work and its dependencies.
- `Plan` validates unique task IDs, dependency references, and acyclicity.
- `TaskPlanner` currently accepts explicit task specifications.
- `AsyncExecutor` executes dependency layers and runs independent tasks
  concurrently up to a configured limit.
- `Provider` is an async protocol. Implementations are registered explicitly.

The executor returns structured outcomes and records exception class names
only, avoiding persistence of exception messages that may contain sensitive
input. This is not a substitute for a complete security review.
