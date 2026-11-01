# Built-in catalog: 50 plugins + 50 skills

Plug includes a first-party catalog definition in `plug/builtin_catalog.py`.
It uses only the Python standard library and contains exactly 50 plugin
implementations and 50 task skills.

## Install the catalog

From the repository root, run:

```bash
python -m plug.builtin_catalog --install
```

This creates:

- `plug/plugins/catalog/<plugin-id>/plugin.json` and `plugin.py` for each of
  the 50 plugins.
- `plug/skills/catalog/<skill-id>/SKILL.md` and `scripts/main.py` for each of
  the 50 skills.

The installer refuses to overwrite existing item folders. If installation
stops because a folder already exists, inspect that folder rather than deleting
or overwriting it.

## Plugin list

| Plugin | Function |
|---|---|
| text-stats | Count characters, words, and lines |
| text-clean | Normalize whitespace |
| text-slug | Create URL-friendly slugs |
| text-extract | Extract regex matches |
| json-format | Validate and pretty-print JSON |
| json-query | Look up nested JSON values |
| csv-stats | Inspect CSV rows and columns |
| csv-filter | Filter CSV rows by exact value |
| math-calc | Safe basic arithmetic |
| datetime-convert | Convert ISO date-time to UTC and Unix time |
| uuid-generate | Generate UUIDs |
| text-hash | Hash text |
| base64-encode | Encode Base64 |
| base64-decode | Decode validated Base64 |
| url-encode | Percent-encode URL components |
| regex-match | Find regular-expression matches |
| text-diff | Generate unified text diffs |
| files-list | List directory entries |
| files-read | Read UTF-8 text files |
| files-write | Write UTF-8 text files |
| archive-inspect | Inspect ZIP contents without extraction |
| python-check | Check Python syntax |
| xml-parse | Inspect XML structure |
| html-extract | Extract title and readable text from HTML |
| url-parse | Parse URL components without network access |
| markdown-toc | Build a table of contents from Markdown headings. |
| markdown-links | Extract Markdown link labels and destinations. |
| text-dedupe-lines | Remove repeated lines and keep their first occurrence. |
| text-sort-lines | Sort text lines alphabetically with optional reverse order. |
| text-case | Convert text into upper, lower, title, or sentence case. |
| word-frequency | Count word frequency and return the most common terms. |
| html-links | Extract anchor links from HTML source. |
| json-flatten | Flatten nested JSON objects and arrays into dotted paths. |
| csv-to-json | Convert CSV records into a JSON array of objects. |
| toml-parse | Parse TOML configuration using Python's tomllib. |
| markdown-table | Build a Markdown table from headers and rows. |
| markdown-to-text | Convert Markdown source into readable plain text. |
| text-wrap | Wrap text paragraphs to a configurable width. |
| text-mask-secrets | Mask likely credentials in text before sharing or logging. |
| regex-replace | Replace regex matches with a supplied replacement string. |
| html-clean | Convert HTML source into text while skipping script and style blocks. |
| json-merge | Merge two JSON objects; right-side keys take precedence. |
| json-pointer | Look up nested JSON values using a slash-separated pointer. |
| csv-column-select | Select and reorder requested CSV columns. |
| csv-sort | Sort CSV rows by a selected column. |
| csv-dedupe | Remove duplicate CSV rows based on selected columns. |
| ini-parse | Parse INI sections and key-value settings. |
| color-contrast | Calculate WCAG contrast ratio between two hexadecimal colors. |
| web-fetch | Fetch public HTTP(S) page text; requires network.read and does not run JavaScript. |
| url-query-parse | Parse URL query parameters into a structured mapping. |

File plugins require explicit `filesystem.read` or `filesystem.write`
permissions through the existing registry. They are local filesystem tools;
they do not upload files.

## Skill list

text-editing, summarization, translation, research-brief, brainstorming,
project-planning, debugging, code-review, python-development, lua-development,
api-integration, data-cleaning, spreadsheet-analysis, documentation,
test-design, security-review, privacy-review, ui-ux-design, brand-naming,
logo-brief, email-writing, meeting-notes, learning-coach, decision-analysis,
incident-response.

Skills are instruction packages. Their helper scripts provide a small
entrypoint and do not autonomously perform external actions. The skill loader
selects them by trigger/description keyword overlap; it is deterministic, not
an LLM semantic router.

Additional task skills: ui-builder, web-research, video-analysis, image-creation, audio-transcription, frontend-development, backend-development, browser-automation, accessibility-audit, data-visualization.

Additional skills: web-page-reading, video-storyboard, video-captioning, audio-analysis, audio-cleanup, ux-writing, component-library, mobile-ui-design, design-system, prompt-engineering, test-automation, ci-cd, deployment-readiness, observability, documentation-review.

## Verify

```bash
python -m unittest tests.test_builtin_catalog -v
```

The tests verify exact counts, installation, discovery, execution of every
plugin handler, safe calculator behavior, and overwrite protection.

## Security and connection status

`web-fetch` requires the explicit `network.read` permission. It accepts public HTTP(S) URLs on standard ports, blocks non-public resolved addresses and validates redirect destinations, supports text responses only, and caps the response body at 1 MB. It does not run JavaScript or automate authenticated browser sessions.

All 50 plugins are local standard-library operations. No cloud account, API
key, network access, or MCP server is required. The ZIP inspector lists entries
but does not extract them. URL parsing does not make requests. File access is
permission-gated, but plugins execute as trusted in-process Python and are not
a hardened sandbox. Review plugin code and grant only the permissions needed.
