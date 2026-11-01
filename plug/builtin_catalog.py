"""First-party Plug catalog: 25 working local plugins and 25 practical skills.

Run `python -m plug.builtin_catalog --install` to materialize the catalog under
`plug/plugins/catalog` and `plug/skills/catalog`.
All plugins use the Python standard library. File access is permission-gated.
"""

from __future__ import annotations

import ast
import base64
import csv
import difflib
import hashlib
import html
import io
import json
import math
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlparse, urlunparse
import xml.etree.ElementTree as ET


def _text_stats(a):
    value = str(a.get("text", ""))
    return {"characters": len(value), "words": len(value.split()), "lines": len(value.splitlines())}


def _text_clean(a):
    value = str(a.get("text", ""))
    mode = a.get("mode", "trim")
    if mode == "trim":
        result = "\n".join(line.strip() for line in value.splitlines()).strip()
    elif mode == "collapse":
        result = re.sub(r"\s+", " ", value).strip()
    elif mode == "blank-lines":
        result = re.sub(r"\n{3,}", "\n\n", value).strip()
    else:
        raise ValueError("mode must be trim, collapse, or blank-lines")
    return {"text": result}


def _text_slug(a):
    value = str(a.get("text", "")).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return {"slug": value}


def _text_extract(a):
    value = str(a.get("text", ""))
    pattern = str(a.get("pattern", r"https?://\S+"))
    return {"matches": re.findall(pattern, value, re.MULTILINE)}


def _json_format(a):
    raw = a.get("json", a.get("text", ""))
    obj = json.loads(raw) if isinstance(raw, str) else raw
    return {"json": json.dumps(obj, ensure_ascii=False, indent=int(a.get("indent", 2)), sort_keys=bool(a.get("sort_keys", False)))}


def _json_query(a):
    obj = a.get("json", a.get("data"))
    if isinstance(obj, str):
        obj = json.loads(obj)
    path = str(a.get("path", "")).strip(".")
    current = obj
    if path:
        for part in path.split("."):
            current = current[int(part)] if isinstance(current, list) else current[part]
    return {"value": current}


def _csv_stats(a):
    rows = list(csv.DictReader(io.StringIO(str(a.get("csv", "")))))
    columns = list(rows[0]) if rows else []
    return {"rows": len(rows), "columns": columns, "non_empty": {c: sum(bool((r.get(c) or "").strip()) for r in rows) for c in columns}}


def _csv_filter(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    column, expected = str(a.get("column", "")), str(a.get("equals", ""))
    if column not in (reader.fieldnames or []):
        raise ValueError("column not found")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
    writer.writeheader()
    matched = [row for row in reader if row.get(column) == expected]
    writer.writerows(matched)
    return {"csv": output.getvalue(), "matched": len(matched)}


_ALLOWED_BIN = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)


def _safe_math(node):
    if isinstance(node, ast.Expression):
        return _safe_math(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN:
        left, right = _safe_math(node.left), _safe_math(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("exponent too large")
        operations = {ast.Add: lambda: left + right, ast.Sub: lambda: left - right,
                      ast.Mult: lambda: left * right, ast.Div: lambda: left / right,
                      ast.FloorDiv: lambda: left // right, ast.Mod: lambda: left % right,
                      ast.Pow: lambda: left ** right}
        return operations[type(node.op)]()
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        value = _safe_math(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    raise ValueError("only numeric literals and basic arithmetic are allowed")


def _math_calc(a):
    expression = str(a.get("expression", ""))
    if len(expression) > 500:
        raise ValueError("expression too long")
    return {"result": _safe_math(ast.parse(expression, mode="eval"))}


def _datetime_convert(a):
    raw = str(a.get("value", ""))
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return {"utc": parsed.astimezone(timezone.utc).isoformat(), "unix": parsed.timestamp()}


def _uuid_generate(a):
    count = max(1, min(int(a.get("count", 1)), 100))
    return {"uuids": [str(uuid.uuid4()) for _ in range(count)]}


def _hash_text(a):
    algorithm = str(a.get("algorithm", "sha256")).lower()
    if algorithm not in hashlib.algorithms_guaranteed:
        raise ValueError("unsupported hash algorithm")
    digest = hashlib.new(algorithm, str(a.get("text", "")).encode()).hexdigest()
    return {"algorithm": algorithm, "digest": digest}


def _base64_encode(a):
    raw = str(a.get("text", "")).encode()
    return {"base64": base64.b64encode(raw).decode("ascii")}


def _base64_decode(a):
    raw = base64.b64decode(str(a.get("base64", "")), validate=True)
    return {"text": raw.decode("utf-8")}


def _url_encode(a):
    return {"encoded": quote(str(a.get("text", "")), safe="")}


def _url_decode(a):
    return {"decoded": unquote(str(a.get("text", "")))}


def _regex_match(a):
    pattern, value = str(a.get("pattern", "")), str(a.get("text", ""))
    if len(pattern) > 1000:
        raise ValueError("pattern too long")
    matches = [m.group(0) for m in re.finditer(pattern, value)]
    return {"matches": matches, "count": len(matches)}


def _text_diff(a):
    left = str(a.get("before", "")).splitlines(True)
    right = str(a.get("after", "")).splitlines(True)
    return {"diff": "".join(difflib.unified_diff(left, right, fromfile="before", tofile="after"))}


def _files_list(a, context):
    context.require("filesystem.read")
    root = Path(str(a.get("path", "."))).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("path is not a directory")
    limit = max(1, min(int(a.get("limit", 100)), 500))
    return {"path": str(root), "entries": [{"name": p.name, "is_dir": p.is_dir(), "size": p.stat().st_size if p.is_file() else None} for p in sorted(root.iterdir())[:limit]]}


def _files_read(a, context):
    context.require("filesystem.read")
    path = Path(str(a.get("path", ""))).expanduser().resolve()
    limit = max(1, min(int(a.get("max_chars", 20000)), 100000))
    return {"text": path.read_text(encoding="utf-8")[:limit], "path": str(path)}


def _files_write(a, context):
    context.require("filesystem.write")
    path = Path(str(a.get("path", ""))).expanduser().resolve()
    if not path.name:
        raise ValueError("a file path is required")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(a.get("text", "")), encoding="utf-8")
    return {"written": str(path), "bytes": path.stat().st_size}


def _archive_inspect(a):
    raw = a.get("path")
    if not raw:
        raise ValueError("path is required")
    path = Path(str(raw)).expanduser().resolve()
    with zipfile.ZipFile(path) as archive:
        return {"entries": [{"name": i.filename, "size": i.file_size, "compressed_size": i.compress_size} for i in archive.infolist()[:500]]}


def _python_check(a):
    source = str(a.get("source", ""))
    ast.parse(source)
    return {"valid": True, "lines": len(source.splitlines())}


def _xml_parse(a):
    root = ET.fromstring(str(a.get("xml", "")))
    return {"root": root.tag, "children": [child.tag for child in list(root)], "text": (root.text or "").strip()}


def _html_extract(a):
    source = str(a.get("html", ""))
    title = re.search(r"<title[^>]*>(.*?)</title>", source, re.I | re.S)
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", source)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return {"title": html.unescape(title.group(1).strip()) if title else "", "text": re.sub(r"\s+", " ", html.unescape(text)).strip()}


def _url_parse(a):
    parsed = urlparse(str(a.get("url", "")))
    return {"scheme": parsed.scheme, "host": parsed.hostname, "port": parsed.port, "path": parsed.path, "query": parsed.query, "fragment": parsed.fragment}


def _runtime_info(a):
    return {"python": sys.version.split()[0], "implementation": sys.implementation.name, "platform": sys.platform, "executable": sys.executable}


PLUGIN_DEFINITIONS = [
    ("text-stats", "Text Statistics", "Count characters, words and lines.", ("text", "count", "words"), _text_stats),
    ("text-clean", "Text Cleaner", "Trim and normalize whitespace.", ("text", "clean", "whitespace"), _text_clean),
    ("text-slug", "Slug Generator", "Convert text into URL-friendly slugs.", ("slug", "url", "text"), _text_slug),
    ("text-extract", "Pattern Extractor", "Extract regex matches from text.", ("extract", "pattern", "regex"), _text_extract),
    ("json-format", "JSON Formatter", "Validate and pretty-print JSON.", ("json", "format", "pretty"), _json_format),
    ("json-query", "JSON Path Lookup", "Read a nested JSON value using a simple dotted path.", ("json", "lookup", "query"), _json_query),
    ("csv-stats", "CSV Statistics", "Inspect CSV columns and non-empty values.", ("csv", "statistics", "data"), _csv_stats),
    ("csv-filter", "CSV Filter", "Filter CSV rows by exact column value.", ("csv", "filter", "rows"), _csv_filter),
    ("math-calc", "Safe Calculator", "Evaluate basic arithmetic without eval or code execution.", ("math", "calculate", "calculator"), _math_calc),
    ("datetime-convert", "Date Time Converter", "Convert ISO date-time values to UTC and Unix time.", ("date", "time", "timezone"), _datetime_convert),
    ("uuid-generate", "UUID Generator", "Generate random UUID identifiers.", ("uuid", "id", "identifier"), _uuid_generate),
    ("text-hash", "Text Hash", "Hash text using a supported hashlib algorithm.", ("hash", "sha256", "digest"), _hash_text),
    ("base64-encode", "Base64 Encoder", "Encode UTF-8 text as Base64.", ("base64", "encode"), _base64_encode),
    ("base64-decode", "Base64 Decoder", "Decode validated Base64 as UTF-8 text.", ("base64", "decode"), _base64_decode),
    ("url-encode", "URL Encoder", "Percent-encode text for URL components.", ("url", "encode", "percent"), _url_encode),
    ("regex-match", "Regex Matcher", "Find regular-expression matches in text.", ("regex", "match", "pattern"), _regex_match),
    ("text-diff", "Text Diff", "Create a unified diff between two texts.", ("diff", "compare", "text"), _text_diff),
    ("files-list", "File Listing", "List directory entries with metadata; requires filesystem.read.", ("files", "folder", "directory", "list"), _files_list),
    ("files-read", "File Reader", "Read a UTF-8 text file; requires filesystem.read.", ("files", "read", "open"), _files_read),
    ("files-write", "File Writer", "Write UTF-8 text to a file; requires filesystem.write.", ("files", "write", "save"), _files_write),
    ("archive-inspect", "ZIP Inspector", "List entries in a ZIP archive without extracting.", ("zip", "archive", "inspect"), _archive_inspect),
    ("python-check", "Python Syntax Checker", "Parse Python source and report syntax validity.", ("python", "syntax", "lint", "code"), _python_check),
    ("xml-parse", "XML Inspector", "Parse XML and report root and direct children.", ("xml", "parse", "inspect"), _xml_parse),
    ("html-extract", "HTML Text Extractor", "Extract page title and readable text from HTML source.", ("html", "extract", "title", "text"), _html_extract),
    ("url-parse", "URL Parser", "Split a URL into its components without making a network request.", ("url", "parse", "host"), _url_parse),
]

SKILL_DEFINITIONS = [
    ("text-editing", "Edit and improve text while preserving the author's meaning.", "rewrite, polish, proofread, edit text", "Identify the intended audience and tone. Correct grammar and clarity without changing facts. Preserve names, numbers, and constraints. Return the revised text and briefly note substantive changes."),
    ("summarization", "Create faithful summaries at the requested level of detail.", "summarize, summary, shorten, key points", "Read the full supplied material. Separate central claims, evidence, decisions, and open questions. Do not add facts. Match the requested length and retain important caveats."),
    ("translation", "Translate text naturally while preserving meaning and formatting.", "translate, translation, bahasa, english", "Identify source and target languages. Preserve names, numbers, tone, and formatting. Translate idioms naturally; flag genuinely ambiguous phrases rather than inventing meaning."),
    ("research-brief", "Structure research questions and evidence into a concise brief.", "research, investigate, sources, report", "Clarify the question and date sensitivity. Prefer primary and authoritative sources. Separate verified facts from interpretation. Cite claims and list unresolved gaps."),
    ("brainstorming", "Generate varied, practical ideas against explicit constraints.", "brainstorm, ideas, concepts, suggestions", "Extract constraints first. Generate distinct options, avoid superficial rewordings, and assess feasibility. Highlight the strongest options with reasons."),
    ("project-planning", "Turn a goal into milestones, tasks, dependencies, and checks.", "project plan, roadmap, milestones, tasks", "Define outcome and scope. Break work into verifiable milestones. Identify dependencies, risks, owners, and acceptance criteria. Avoid pretending unstarted work is complete."),
    ("debugging", "Diagnose software defects systematically using evidence.", "debug, bug, error, traceback, fix", "Reproduce the issue from supplied evidence. Locate the failing layer. Propose the smallest safe fix, add a regression test, and report what was actually run."),
    ("code-review", "Review code for correctness, security, maintainability, and regressions.", "review code, audit, inspect script", "Trace execution paths and inputs. Prioritize concrete defects with file and line references. Distinguish bugs from style. Suggest tests and do not rewrite unrelated code."),
    ("python-development", "Build maintainable Python features with tests and clear interfaces.", "python, script, package, function", "Inspect existing project conventions first. Use supported Python versions and standard libraries where practical. Validate inputs, handle errors, and add focused unit tests."),
    ("lua-development", "Write and debug Lua scripts with clear runtime assumptions.", "lua, roblox, luau, script", "Confirm whether target is Lua or Luau and identify available APIs. Avoid inventing services or exploit-only assumptions. Keep functions modular and explain required environment."),
    ("api-integration", "Design reliable API clients with explicit authentication and failure handling.", "api, endpoint, integration, webhook", "Read the official API contract. Keep secrets out of source and logs. Set timeouts, validate responses, handle rate limits, and test with mocked responses before live use."),
    ("data-cleaning", "Normalize tabular data while preserving traceability.", "clean data, csv, spreadsheet, normalize", "Inspect schema and missing values. Define transformations before applying them. Preserve the original input, report changed rows, and validate output types and counts."),
    ("spreadsheet-analysis", "Analyze spreadsheet data and explain formulas and trends.", "excel, spreadsheet, xlsx, formula", "Inspect sheets, headers, formulas, and units. Check missing or duplicate values. Show calculations transparently and distinguish correlation from causation."),
    ("documentation", "Write accurate developer and user documentation from actual behavior.", "documentation, readme, docs, guide", "Inspect the implementation before documenting it. Include prerequisites, examples, errors, permissions, and limitations. Never document planned behavior as implemented."),
    ("test-design", "Create meaningful tests for normal, edge, and failure cases.", "tests, unit test, test cases, coverage", "Derive tests from public behavior. Cover success, invalid input, boundaries, permissions, and regressions. Keep tests deterministic and independent."),
    ("security-review", "Assess code and workflows for practical security risks.", "security, vulnerability, threat model, permissions", "Identify assets, trust boundaries, and attacker-controlled inputs. Check secrets, path traversal, injection, permissions, and unsafe execution. Rank findings by impact and likelihood."),
    ("privacy-review", "Minimize personal data exposure and explain data flows.", "privacy, personal data, data handling", "Map what data is collected, stored, transmitted, and retained. Minimize collection. Require consent for external sharing and avoid exposing secrets or identifiers."),
    ("ui-ux-design", "Improve interface usability, hierarchy, consistency, and accessibility.", "ui, ux, interface, panel, design", "Identify the primary user task. Improve visual hierarchy, spacing, states, feedback, and accessibility. Preserve functional controls and consider small screens and performance."),
    ("brand-naming", "Create distinctive, readable brand names and screen obvious conflicts.", "brand name, naming, name ideas, gaming brand", "Define tone, length, pronunciation, and audience. Generate pronounceable candidates. Search for obvious existing uses when web access is requested; never guarantee trademark availability."),
    ("logo-brief", "Turn brand direction into a precise, original logo brief.", "logo, branding, icon, emblem", "Extract brand personality, use cases, and colors. Specify silhouette, typography, contrast, and small-size behavior. Use references for direction, not copying."),
    ("email-writing", "Draft clear emails matched to recipient and purpose.", "email, reply email, inbox message", "Identify recipient relationship, goal, and desired tone. Put the ask near the top. Keep facts accurate and avoid inventing commitments or attachments."),
    ("meeting-notes", "Convert rough notes into decisions, actions, and open questions.", "meeting, minutes, action items, notes", "Separate discussion from decisions. Capture action, owner, and due date only when stated. List unresolved questions and preserve important context."),
    ("learning-coach", "Explain difficult topics progressively with examples and checks.", "learn, explain, teach, tutorial", "Start from the learner's stated level. Explain one concept at a time, give a concrete example, check understanding, and correct misconceptions without shaming."),
    ("decision-analysis", "Compare options against explicit criteria and trade-offs.", "decide, compare options, pros cons, recommendation", "List options and decision criteria. Distinguish facts from assumptions. Compare trade-offs, identify reversibility, and recommend only when evidence supports it."),
    ("incident-response", "Organize a safe, evidence-led response to technical incidents.", "incident, outage, production issue, recovery", "Stabilize first and preserve evidence. Establish timeline and impact. Avoid destructive actions without approval. Track mitigations, verification, and follow-up prevention."),
]

def run_builtin(context, arguments):
    """Execute the built-in plugin matching context.plugin_id."""
    plugin_id = context.plugin_id
    handlers = {item[0]: item[4] for item in PLUGIN_DEFINITIONS}
    if plugin_id not in handlers:
        raise KeyError(f"unknown built-in plugin: {plugin_id}")
    args = dict(arguments or {})
    if plugin_id == "files-list":
        return handlers[plugin_id](args, context)
    if plugin_id in {"files-read", "files-write"}:
        return handlers[plugin_id](args, context)
    return handlers[plugin_id](args)


def install_builtin_catalog(plugin_root=None, skill_root=None):
    """Materialize all 25 plugins and 25 skills; never overwrite existing files."""
    import json as _json
    from pathlib import Path as _Path
    base = _Path(__file__).resolve().parent
    plugins = _Path(plugin_root) if plugin_root else base / "plugins" / "catalog"
    skills = _Path(skill_root) if skill_root else base / "skills" / "catalog"
    plugins.mkdir(parents=True, exist_ok=True)
    skills.mkdir(parents=True, exist_ok=True)
    for plugin_id, name, description, keywords, handler in PLUGIN_DEFINITIONS:
        folder = plugins / plugin_id
        folder.mkdir(exist_ok=False)
        permissions = ["filesystem.read"] if plugin_id in {"files-list", "files-read"} else (["filesystem.write"] if plugin_id == "files-write" else [])
        manifest = {"id": plugin_id, "name": name, "version": "1.0.0", "description": description,
                    "entrypoint": "plugin.py", "capabilities": ["local-processing"],
                    "permissions": permissions, "keywords": list(keywords)}
        (folder / "plugin.json").write_text(_json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (folder / "plugin.py").write_text(
            '"""Built-in Plug plugin. Implementation lives in plug.builtin_catalog."""\n'
            'from plug.builtin_catalog import run_builtin\n\n'
            'def run(context, arguments):\n'
            '    return run_builtin(context, arguments)\n', encoding="utf-8")
    for name, description, triggers, instructions in SKILL_DEFINITIONS:
        folder = skills / name
        folder.mkdir(exist_ok=False)
        trigger_line = ", ".join(x.strip() for x in triggers.split(","))
        (folder / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\ntriggers: {trigger_line}\n---\n\n"
            f"# {name.replace('-', ' ').title()}\n\n{instructions}\n",
            encoding="utf-8")
        (folder / "scripts").mkdir()
        (folder / "scripts" / "main.py").write_text(
            f'"""Helper entrypoint for the {name} skill."""\n\n'
            f'SKILL_NAME = "{name}"\n\n'
            'def run(arguments=None):\n'
            '    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), '
            '"instructions_file": "SKILL.md"}\n', encoding="utf-8")
    return {"plugins": len(PLUGIN_DEFINITIONS), "skills": len(SKILL_DEFINITIONS),
            "plugin_root": str(plugins), "skill_root": str(skills)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Install Plug's 25 built-in plugins and 25 skills.")
    parser.add_argument("--install", action="store_true", help="materialize the bundled catalog")
    args = parser.parse_args()
    if args.install:
        print(json.dumps(install_builtin_catalog(), indent=2))
    else:
        parser.print_help()
