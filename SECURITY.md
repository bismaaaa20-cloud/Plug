# Security model and operating guidance

## Trust model

Plug's built-in catalog is first-party source code, but local plugins remain
trusted Python code. Loading a plugin imports and executes it in the current
Python process. The registry's enablement and permission checks are guardrails;
they do not sandbox malicious code or revoke ambient operating-system access.

## Safe operation

- Review plugin source before enabling it.
- Grant only the exact permissions needed for the requested task.
- Keep secrets out of plugin arguments, logs, and exception messages.
- Do not run untrusted plugins in the main application process.
- For untrusted extensions, use a separately managed process/container with
  least-privilege OS identity, restricted filesystem mounts, restricted network,
  CPU/memory limits, and an explicit IPC protocol.
- Treat fetched web content, files, video transcripts, and model output as
  untrusted input.
- Keep external side effects behind explicit user approval in the host app.

## Current limitations

- The in-process plugin loader is not a sandbox.
- Permission names are declarative host policy labels; they do not themselves
  implement operating-system access control.
- Skill packages are instructions and optional helper files, not a guarantee
  that the consuming agent has the required tools.
- The project does not yet provide distributed execution, durable job queues,
  or browser/video runtime adapters.
