# Capability matrix

The catalog contains **200 distinct plugin packages** and **200 distinct skill packages**.
These are first-party items authored for Plug. A package count is not the same as
a count of connected third-party services.

## What works as a plugin today

| Area | Available capability | Status / boundary |
|---|---|---|
| Text and documents | Clean, compare, transform, extract, mask, and summarize text; Markdown helpers | Local Python functions |
| Data | CSV/JSON/TOML/INI processing, statistics, filtering, conversion | Local Python functions |
| Code | Python syntax/AST checks, Lua/JS source inspection, Git diff statistics | Static/local analysis; not a full compiler or runtime |
| Files | Read, write, search, copy, rename, checksum, directory and archive operations | Permission-gated local filesystem access |
| Web | `web-fetch` reads public HTTP(S) page text | Requires `network.read`; no JavaScript execution, login, or interactive browser automation |
| UI design | `ui-builder` skill gives a design and implementation workflow | Requires an agent with coding and file tools; no standalone visual UI generator plugin yet |
| Video | `video-analysis` skill specifies a careful analysis workflow | Requires supplied video data and a video-capable model/tool; no standalone video decoder/player plugin |
| Image and audio | Image/audio skills describe workflows for available multimodal tools | Requires corresponding image/audio capability; catalog does not itself generate or decode media |

## Skill responsibilities

Skills are task-specific instruction packages, not executable integrations.
Examples:

- **ui-builder**: map user flows, define responsive layout/components/states, implement real controls, and test.
- **web-research / browser-research**: retrieve pages using an available web/browser connector, verify claims, and cite sources.
- **video-analysis / video-storyboard / video-captioning**: analyze accessible footage, plan scenes, or review captions when video data/tools are available.
- **image-creation / image-asset-pipeline**: create or manage visual assets when an image-generation/editing tool is available.
- **frontend-development / backend-development**: implement application code using the project's actual stack.
- **accessibility-audit / web-accessibility-testing**: inspect semantic structure, keyboard access, labels, focus, and contrast.

Each skill has its own `SKILL.md` with its scope, triggers, and workflow. The skill
router currently uses deterministic keyword overlap; it is not an LLM semantic
router and does not automatically grant permissions.

## Connection and safety boundaries

- Plugin code runs as trusted in-process Python, not in a hardened sandbox.
- Plugins are disabled until explicitly enabled and permission grants are provided.
- Filesystem and network capabilities must be granted explicitly.
- No live authenticated browser session, video stream, or third-party API account is
  implied by the presence of a skill.
- Report an integration as connected only after its adapter, credentials/permissions,
  and tests are actually configured.
