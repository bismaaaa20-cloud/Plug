# Adaptive Teamwork Algorithm

Plug's team coordinator is interface-neutral. An agent can eventually be backed
by a local model, desktop app, browser session, or another explicitly supported
adapter. The allocator does not assume API access.

## 1. Strategy selection

The strategy engine examines task count, dependencies, priority, and complexity:

- **Direct**: one focused task.
- **Parallel**: independent tasks can be handled at the same time.
- **Pipeline**: dependent tasks wait for prerequisites; independent branches can
  still run concurrently.
- **Collaborative**: complex or high-priority work benefits from multiple views.
- **Review**: a review is required for complex/high-priority plans or larger plans.

## 2. Agent selection

For each ready task, Plug scores eligible agents using:

- 55% skill match
- 25% reliability
- 10% task-category preference
- 10% load penalty

The score is deterministic and explainable. Ties are resolved consistently.
Capacity is treated as a concurrency hint; a static assignment is still made
when all agents have reached their preferred capacity.

## 3. Friendly coordination

Status messages should be calm, concise, respectful, and actionable. Revisions
describe what to improve rather than blaming an agent. The user remains in
control of risky actions and final approvals.

## 4. Desktop integration boundary

This algorithm only allocates work. It does not pretend to control desktop apps
or browser tabs. A future desktop adapter must explicitly declare how it
connects, sends input, receives output, handles login/session state, and asks
for human approval when needed. No API key is required by this algorithm.
