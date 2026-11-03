# Plug 6,000-item expansion plan

## Target

Grow the first-party catalog from 200 plugins + 200 skills to **3,000 plugins + 3,000 skills**. The target is 6,000 distinct, documented items—not 6,000 renamed copies or generated placeholders.

The existing 200 + 200 catalog remains intact while the expansion is built in validated batches.

## Definition of a real plugin

Every plugin must have:
- A unique stable ID and one clearly bounded primary job.
- A manifest with purpose, triggers/keywords, input contract, output contract, required permissions, and dependencies.
- An executable entrypoint that performs the advertised operation or returns a clear configuration/dependency error.
- Unit tests for normal, invalid, and permission-denied cases.
- No embedded credentials. External services use environment/secret configuration.
- A capability status: `local`, `external-config-required`, or `optional-dependency-required`.

A plugin must not claim to create media, browse authenticated pages, or control an app unless the required provider/runtime is installed and connected.

## Definition of a real skill

Every skill must have:
- A unique name, description, and specific trigger phrases.
- A distinct task scope and workflow—not just a different title.
- Required inputs, expected deliverables, quality checks, and escalation/failure behavior.
- Tool requirements declared explicitly (for example browser, image generation, video understanding, filesystem, or a connected app).
- At least one validation fixture or test that checks its metadata and required sections.

Skills guide an agent. They do not create a missing model, API, browser, or media codec.

## Product families

The 3,000 plugins and 3,000 skills will be organized by task families, including:
1. Web research, crawling, extraction, source verification, and monitoring.
2. Browser control, web testing, accessibility, and website operations.
3. Image generation/editing, image understanding, asset processing, and design.
4. Video generation/planning, editing, captioning, transcription, and analysis.
5. Audio generation, transcription, cleanup, speech, and sound design.
6. YouTube/channel research, video planning, metadata, publishing workflows, and analytics.
7. Writing, translation, documents, presentations, and knowledge management.
8. UI/UX, frontend, backend, mobile, game development, and code quality.
9. Data analysis, spreadsheets, databases, statistics, and visualization.
10. Business operations, CRM, marketing, sales, support, and project management.
11. Productivity, calendar, email, files, and collaboration.
12. Security, privacy, compliance, testing, and reliability.
13. Education, research, science, and professional workflows.
14. Developer infrastructure, cloud, deployment, observability, and automation.
15. Personal utilities and device workflows.

The catalog generator must reject duplicate IDs, duplicate capability signatures, missing contracts, and items that only differ by wording.

## Five native Plug integrations (MCP-independent)

These are Plug plugins with direct API or local-runtime adapters. They do not require an MCP server.

| Plug plugin | Intended capability | Connection boundary |
|---|---|---|
| Perplexity Research | Search/research, grounded answers, source metadata and citations | Perplexity API key and explicitly configured supported API |
| Firecrawl Web Data | Search, scrape, map/crawl, extract structured web content | Firecrawl API key; bounded URLs, jobs, response sizes and rate limits |
| PostHog Analytics | Read/query events and insights; manage insight metadata only when explicitly authorized | Correct US/EU/self-hosted host, project ID, scoped API key/OAuth; read-only by default |
| Playwright Browser | Launch isolated browser contexts, navigate, inspect DOM, screenshot, click, fill and test | Optional Playwright dependency and browser binaries; explicit domain and action permissions |
| Composio App Connect | Discover allowed toolkits/actions, connect accounts, invoke approved actions | Composio API key and user-authorized connected accounts; per-tool allowlist and approval gates |

The implementation must follow current official API contracts, not copy an MCP server protocol. Provider credentials must never appear in logs, manifests, test fixtures, or returned errors. Destructive actions and external writes require explicit permission and approval.

Official references:
- Perplexity API: https://www.perplexity.ai/api-platform
- Firecrawl API: https://docs.firecrawl.dev/
- PostHog API: https://posthog.com/docs/api
- Playwright Python: https://playwright.dev/python/docs/intro
- Composio API: https://docs.composio.dev/reference

## Plug AI Browser

Build a separate desktop application named **Plug AI Browser**, using the open-source Chromium engine and Playwright/CDP automation.

The first release should be a browser shell with:
- Tab and window management, address bar, navigation, back/forward/reload.
- Isolated browser profiles/contexts and explicit profile selection.
- AI page understanding: visible text, page structure, links, forms, and screenshots.
- An action planner that proposes click/type/navigate actions and shows the target before execution.
- Human approval for sign-in, purchases, posting, sending messages, deleting data, downloads, and other consequential actions.
- Domain allowlists, permission prompts, download controls, secret isolation, and action logs.
- A local bridge to Plug's plugin runtime; no remote-control endpoint exposed by default.

Use Chromium as the engine; do not claim this is Google's proprietary Chrome or redistribute Google Chrome branding. A full Chromium fork is a separate, high-maintenance engineering project. Start with an independently branded Chromium-based app shell and only fork Chromium if a later requirement truly needs engine-level changes.

## Media creation capability model

Plug should expose provider-neutral interfaces for image, audio, video, and text generation. The plugin owns workflow, input validation, file handling, metadata, and post-processing; a configured model/provider performs generation or multimodal inference. YouTube workflows can plan, script, edit, caption, package, and publish only when the required media tools and YouTube account scopes are connected.

Never report a generated video/image/audio file or a published YouTube item unless the provider/runtime returned a verifiable artifact or publication ID.

## Delivery phases

1. **Foundation:** capability contracts, catalog generator, category taxonomy, duplicate detection, test fixtures, and manifest versioning.
2. **Core integrations:** implement and test the five native integrations above with configuration documentation and mock HTTP/local-browser tests.
3. **AI Browser MVP:** desktop shell, Chromium runtime, Playwright bridge, tab/profile management, approval UI, and audit log.
4. **Media and creator workflows:** image/audio/video adapters, YouTube workflows, asset pipeline, and artifact verification.
5. **Catalog batches:** grow plugin and skill catalogs in reviewable batches; every batch runs uniqueness, contract, execution, permission, and regression tests.
6. **Release gate:** count exactly 3,000 unique plugins and 3,000 unique skills; verify every item, document external dependencies, run the complete Python matrix and desktop-app tests.

## Release gates

The target is not complete until:
- There are exactly 3,000 discoverable plugin IDs and 3,000 discoverable skill names.
- Every plugin entrypoint has a passing test and a documented permission contract.
- Every skill has a distinct task contract and passes metadata/structure checks.
- The five integrations pass mocked API tests and their optional live smoke tests when credentials are supplied.
- AI Browser passes navigation, context isolation, approval, permission, and security tests.
- No provider is marked connected merely because its package exists.
