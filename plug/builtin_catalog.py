"""First-party Plug catalog: 200 plugins and 200 task-specific skills.

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


def _markdown_toc(a):
    lines = []
    for line in str(a.get("markdown", a.get("text", ""))).splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            title = match.group(2).strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            lines.append("  " * (len(match.group(1)) - 1) + f"- [{title}](#{slug})")
    return {"toc": "\n".join(lines), "count": len(lines)}


def _markdown_links(a):
    source = str(a.get("markdown", a.get("text", "")))
    pattern = r"(?<!!)\[([^\]]+)\]\(([^)]+)\)"
    links = [{"label": match.group(1), "url": match.group(2)} for match in re.finditer(pattern, source)]
    return {"links": links, "count": len(links)}


def _text_dedupe_lines(a):
    lines = str(a.get("text", "")).splitlines()
    seen, result = set(), []
    for line in lines:
        key = line if a.get("case_sensitive", True) else line.casefold()
        if key not in seen:
            seen.add(key)
            result.append(line)
    return {"text": "\n".join(result), "removed": len(lines) - len(result)}


def _text_sort_lines(a):
    lines = str(a.get("text", "")).splitlines()
    result = sorted(lines, key=str.casefold, reverse=bool(a.get("reverse", False)))
    return {"text": "\n".join(result)}


def _text_case(a):
    value, mode = str(a.get("text", "")), str(a.get("mode", "lower"))
    choices = {"upper": value.upper(), "lower": value.lower(), "title": value.title(),
               "sentence": value[:1].upper() + value[1:].lower()}
    if mode not in choices:
        raise ValueError("mode must be upper, lower, title, or sentence")
    return {"text": choices[mode]}


def _word_frequency(a):
    from collections import Counter
    words = re.findall(r"\b[\w']+\b", str(a.get("text", "")).casefold())
    limit = max(1, min(int(a.get("limit", 20)), 200))
    return {"words": [{"word": word, "count": count} for word, count in Counter(words).most_common(limit)],
            "total": len(words)}


def _html_links(a):
    source = str(a.get("html", ""))
    pattern = r'''(?is)<a\b[^>]*href\s*=\s*(['"])(.*?)\1[^>]*>(.*?)</a>'''
    links = []
    for match in re.finditer(pattern, source):
        label = re.sub(r"(?s)<[^>]+>", " ", match.group(3))
        links.append({"url": html.unescape(match.group(2)),
                      "label": re.sub(r"\s+", " ", html.unescape(label)).strip()})
    return {"links": links, "count": len(links)}


def _json_flatten(a):
    obj = a.get("json", a.get("data", {}))
    if isinstance(obj, str):
        obj = json.loads(obj)
    output = {}
    def walk(value, prefix):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{prefix}.{key}" if prefix else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{prefix}.{index}" if prefix else str(index))
        else:
            output[prefix] = value
    walk(obj, "")
    return {"flat": output}


def _csv_to_json(a):
    rows = list(csv.DictReader(io.StringIO(str(a.get("csv", "")))))
    return {"rows": rows, "count": len(rows), "json": json.dumps(rows, ensure_ascii=False)}


def _toml_parse(a):
    import tomllib
    data = tomllib.loads(str(a.get("toml", a.get("text", ""))))
    return {"data": data, "keys": list(data)}


def _markdown_table(a):
    headers = [str(v).replace("|", "\\|") for v in a.get("headers", [])]
    rows = a.get("rows", [])
    if not headers: raise ValueError("headers are required")
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        values = [str(v).replace("|", "\\|") for v in row]
        if len(values) != len(headers): raise ValueError("row length must match headers")
        lines.append("| " + " | ".join(values) + " |")
    return {"markdown": "\n".join(lines), "rows": len(rows)}

def _markdown_to_text(a):
    text = str(a.get("markdown", a.get("text", "")))
    fence = chr(96) * 3
    text = re.sub(re.escape(fence) + r".*?" + re.escape(fence), " ", text, flags=re.S)
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"[*_~]", "", text).replace(chr(96), "")
    return {"text": re.sub(r"\n{3,}", "\n\n", text).strip()}

def _text_wrap(a):
    import textwrap
    width = max(10, min(int(a.get("width", 72)), 300))
    parts = str(a.get("text", "")).split("\n\n")
    return {"text": "\n\n".join(textwrap.fill(part, width=width) for part in parts)}

def _text_mask_secrets(a):
    pattern = r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\b(\s*[:=]\s*)([^\s,;]+)"
    text, count = re.subn(pattern, lambda m: m.group(1) + m.group(2) + "[REDACTED]", str(a.get("text", "")))
    return {"text": text, "masked_values": count}

def _regex_replace(a):
    pattern = str(a.get("pattern", ""))
    if len(pattern) > 1000: raise ValueError("pattern too long")
    result, count = re.subn(pattern, str(a.get("replacement", "")), str(a.get("text", "")),
                            count=max(0, min(int(a.get("count", 0)), 10000)))
    return {"text": result, "replacements": count}

def _html_clean(a):
    from html.parser import HTMLParser
    class Extractor(HTMLParser):
        def __init__(self):
            super().__init__(); self.parts = []; self.skip = 0
        def handle_starttag(self, tag, attrs):
            if tag in {"script", "style"}: self.skip += 1
            elif tag in {"p", "div", "br", "li", "h1", "h2", "h3"} and not self.skip: self.parts.append("\n")
        def handle_endtag(self, tag):
            if tag in {"script", "style"} and self.skip: self.skip -= 1
            elif tag in {"p", "div", "li", "h1", "h2", "h3"} and not self.skip: self.parts.append("\n")
        def handle_data(self, data):
            if not self.skip: self.parts.append(data)
    parser = Extractor(); parser.feed(str(a.get("html", "")))
    return {"text": re.sub(r"[ \t]+", " ", "".join(parser.parts)).strip()}

def _json_merge(a):
    left, right = a.get("left", {}), a.get("right", {})
    if isinstance(left, str): left = json.loads(left)
    if isinstance(right, str): right = json.loads(right)
    if not isinstance(left, dict) or not isinstance(right, dict): raise ValueError("both inputs must be JSON objects")
    return {"merged": {**left, **right}}

def _json_pointer(a):
    obj = a.get("json", a.get("data"))
    if isinstance(obj, str): obj = json.loads(obj)
    pointer = str(a.get("pointer", ""))
    if pointer == "": return {"value": obj}
    if not pointer.startswith("/"): raise ValueError("pointer must be empty or begin with /")
    current = obj
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return {"value": current}

def _csv_column_select(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    fields = reader.fieldnames or []
    selected = [v.strip() for v in str(a.get("columns", "")).split(",") if v.strip()]
    if not selected or any(v not in fields for v in selected): raise ValueError("columns must name existing CSV headers")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=selected); writer.writeheader()
    writer.writerows({name: row.get(name, "") for name in selected} for row in reader)
    return {"csv": output.getvalue(), "columns": selected}

def _csv_sort(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    fields, rows, column = reader.fieldnames or [], list(reader), str(a.get("column", ""))
    if column not in fields: raise ValueError("column not found")
    rows.sort(key=lambda row: (row.get(column) or "").casefold(), reverse=bool(a.get("reverse", False)))
    output = io.StringIO()
    if fields:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    return {"csv": output.getvalue(), "count": len(rows)}

def _csv_dedupe(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    fields, rows = reader.fieldnames or [], list(reader)
    selected = [v.strip() for v in str(a.get("columns", "")).split(",") if v.strip()] or fields
    if any(v not in fields for v in selected): raise ValueError("dedupe column not found")
    seen, unique = set(), []
    for row in rows:
        key = tuple(row.get(v) for v in selected)
        if key not in seen: seen.add(key); unique.append(row)
    output = io.StringIO()
    if fields:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(unique)
    return {"csv": output.getvalue(), "removed": len(rows) - len(unique)}

def _ini_parse(a):
    import configparser
    parser = configparser.ConfigParser()
    parser.read_string(str(a.get("ini", a.get("text", ""))))
    return {"sections": {section: dict(parser.items(section)) for section in parser.sections()}}

def _color_contrast(a):
    def luminance(value):
        raw = str(value).lstrip("#")
        if len(raw) == 3: raw = "".join(ch * 2 for ch in raw)
        if not re.fullmatch(r"[0-9a-fA-F]{6}", raw): raise ValueError("colors must be #RGB or #RRGGBB")
        channels = [int(raw[i:i+2], 16) / 255 for i in (0, 2, 4)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    first, second = luminance(a.get("foreground", "#000000")), luminance(a.get("background", "#FFFFFF"))
    ratio = (max(first, second) + 0.05) / (min(first, second) + 0.05)
    return {"ratio": round(ratio, 2), "aa_normal": ratio >= 4.5, "aa_large": ratio >= 3, "aaa_normal": ratio >= 7}

def _assert_public_http_url(value):
    import ipaddress, socket
    from urllib.parse import urlsplit
    parsed = urlsplit(str(value))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("only public HTTP(S) URLs are allowed")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in {80, 443}: raise ValueError("only standard HTTP(S) ports are allowed")
    try:
        addresses = [ipaddress.ip_address(parsed.hostname)]
    except ValueError:
        try: addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)]
        except OSError as exc: raise ValueError("hostname could not be resolved") from exc
    if not addresses or any(not item.is_global for item in addresses):
        raise ValueError("private and non-public network addresses are blocked")


def _web_fetch(a, context):
    import urllib.request
    from urllib.parse import urljoin
    context.require("network.read")
    url = str(a.get("url", ""))
    _assert_public_http_url(url)
    class PublicRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urljoin(req.full_url, newurl)
            _assert_public_http_url(target)
            return super().redirect_request(req, fp, code, msg, headers, target)
    request = urllib.request.Request(url, headers={"User-Agent": "Plug-WebReader/1.0", "Accept": "text/html,text/plain,application/json"})
    opener = urllib.request.build_opener(PublicRedirect())
    with opener.open(request, timeout=10) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "text/plain", "application/json", "text/xml", "application/xml"}:
            raise ValueError("response is not a supported text content type")
        raw = response.read(1000001)
        if len(raw) > 1000000: raise ValueError("page exceeds the 1 MB text limit")
        charset = response.headers.get_content_charset() or "utf-8"
        body = raw.decode(charset, errors="replace")
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
        return {"url": response.geturl(), "status": response.status, "content_type": content_type,
                "title": re.sub(r"\s+", " ", html.unescape(title.group(1))).strip() if title else "",
                "text": body}

def _url_query_parse(a):
    from urllib.parse import parse_qs, urlsplit
    query = urlsplit(str(a.get("url", ""))).query
    parsed = parse_qs(query, keep_blank_values=True)
    return {"parameters": parsed, "keys": list(parsed)}

def _text_reverse(a):
    return {"text": str(a.get("text", ""))[::-1]}

def _text_sentence_count(a):
    text = str(a.get("text", "")).strip()
    endings = re.findall(r"[.!?]+(?=\s|$)", text)
    return {"sentences": len(endings), "endings": endings}

def _text_char_frequency(a):
    from collections import Counter
    counts = Counter(str(a.get("text", "")))
    return {"characters": [{"character": ch, "count": n} for ch, n in counts.most_common()],
            "total": sum(counts.values())}

def _text_remove_blank(a):
    lines = str(a.get("text", "")).splitlines()
    kept = [line for line in lines if line.strip()]
    return {"text": "\n".join(kept), "removed": len(lines) - len(kept)}

def _text_indent(a):
    prefix = str(a.get("prefix", "    "))
    lines = str(a.get("text", "")).splitlines()
    return {"text": "\n".join((prefix + line if line or a.get("indent_blank", False) else line) for line in lines)}

def _text_dedent(a):
    import textwrap
    return {"text": textwrap.dedent(str(a.get("text", "")))}

def _text_number_lines(a):
    start = int(a.get("start", 1))
    width = max(1, len(str(start + len(str(a.get("text", "")).splitlines()))))
    lines = str(a.get("text", "")).splitlines()
    return {"text": "\n".join(f"{start + i:>{width}}: {line}" for i, line in enumerate(lines))}

def _text_truncate(a):
    text = str(a.get("text", ""))
    limit = max(0, min(int(a.get("max_chars", 160)), 1000000))
    suffix = str(a.get("suffix", "…"))
    return {"text": text if len(text) <= limit else text[:limit] + suffix,
            "truncated": len(text) > limit, "original_length": len(text)}

def _text_prefix_lines(a):
    prefix = str(a.get("prefix", ""))
    lines = str(a.get("text", "")).splitlines()
    return {"text": "\n".join(prefix + line if line else line for line in lines)}

def _text_suffix_lines(a):
    suffix = str(a.get("suffix", ""))
    lines = str(a.get("text", "")).splitlines()
    return {"text": "\n".join(line + suffix if line else line for line in lines)}

def _text_unique_words(a):
    words = re.findall(r"\b[\w']+\b", str(a.get("text", "")).casefold())
    unique = list(dict.fromkeys(words))
    return {"words": unique, "count": len(unique)}

def _text_palindrome(a):
    value = re.sub(r"[^a-z0-9]", "", str(a.get("text", "")).casefold())
    return {"normalized": value, "palindrome": value == value[::-1]}

def _text_rot13(a):
    import codecs
    return {"text": codecs.encode(str(a.get("text", "")), "rot_13")}

def _json_keys(a):
    obj = a.get("json", a.get("data", {}))
    if isinstance(obj, str): obj = json.loads(obj)
    if not isinstance(obj, dict): raise ValueError("input must be a JSON object")
    return {"keys": list(obj.keys()), "count": len(obj)}

def _json_values(a):
    obj = a.get("json", a.get("data", {}))
    if isinstance(obj, str): obj = json.loads(obj)
    if not isinstance(obj, dict): raise ValueError("input must be a JSON object")
    return {"values": list(obj.values()), "count": len(obj)}

def _json_types(a):
    obj = a.get("json", a.get("data", {}))
    if isinstance(obj, str): obj = json.loads(obj)
    if not isinstance(obj, dict): raise ValueError("input must be a JSON object")
    def kind(v):
        if v is None: return "null"
        if isinstance(v, bool): return "boolean"
        if isinstance(v, (int, float)): return "number"
        if isinstance(v, str): return "string"
        if isinstance(v, list): return "array"
        return "object"
    return {"types": {key: kind(value) for key, value in obj.items()}}

def _json_array_stats(a):
    items = a.get("json", a.get("items", []))
    if isinstance(items, str): items = json.loads(items)
    if not isinstance(items, list): raise ValueError("input must be a JSON array")
    counts = {}
    for item in items:
        name = "null" if item is None else "boolean" if isinstance(item, bool) else "number" if isinstance(item, (int, float)) else "string" if isinstance(item, str) else "array" if isinstance(item, list) else "object"
        counts[name] = counts.get(name, 0) + 1
    return {"count": len(items), "type_counts": counts}

def _json_sort_keys(a):
    obj = a.get("json", a.get("data", {}))
    if isinstance(obj, str): obj = json.loads(obj)
    return {"json": json.dumps(obj, ensure_ascii=False, indent=int(a.get("indent", 2)), sort_keys=True)}

def _json_minify(a):
    obj = a.get("json", a.get("data", "null"))
    if isinstance(obj, str): obj = json.loads(obj)
    return {"json": json.dumps(obj, ensure_ascii=False, separators=(",", ":"))}

def _csv_column_stats(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    rows, column = list(reader), str(a.get("column", ""))
    if column not in (reader.fieldnames or []): raise ValueError("column not found")
    values = [row.get(column, "") or "" for row in rows]
    filled = [value for value in values if value.strip()]
    return {"column": column, "rows": len(rows), "filled": len(filled),
            "blank": len(rows) - len(filled), "unique": len(set(filled))}

def _csv_head(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    fields, rows = reader.fieldnames or [], list(reader)
    count = max(0, min(int(a.get("count", 5)), 10000))
    output = io.StringIO()
    if fields:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows[:count])
    return {"csv": output.getvalue(), "returned": min(count, len(rows)), "total": len(rows)}

def _csv_tail(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    fields, rows = reader.fieldnames or [], list(reader)
    count = max(0, min(int(a.get("count", 5)), 10000))
    output = io.StringIO()
    if fields:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows[-count:] if count else [])
    return {"csv": output.getvalue(), "returned": min(count, len(rows)), "total": len(rows)}

def _csv_transpose(a):
    rows = list(csv.reader(io.StringIO(str(a.get("csv", "")))))
    transposed = list(zip(*rows)) if rows else []
    output = io.StringIO()
    csv.writer(output).writerows(transposed)
    return {"csv": output.getvalue(), "rows": len(transposed), "columns": len(transposed[0]) if transposed else 0}

def _number_stats(a):
    import statistics
    values = [float(x) for x in a.get("values", [])]
    if not values: raise ValueError("at least one number is required")
    return {"count": len(values), "mean": statistics.fmean(values), "median": statistics.median(values),
            "min": min(values), "max": max(values), "variance": statistics.pvariance(values)}

def _number_percentile(a):
    values = sorted(float(x) for x in a.get("values", []))
    percentile = float(a.get("percentile", 50))
    if not values: raise ValueError("at least one number is required")
    if not 0 <= percentile <= 100: raise ValueError("percentile must be between 0 and 100")
    position = (len(values) - 1) * percentile / 100
    low, high = math.floor(position), math.ceil(position)
    result = values[low] if low == high else values[low] + (values[high] - values[low]) * (position - low)
    return {"percentile": percentile, "value": result}

def _json_escape_string(a):
    return {"json_string": json.dumps(str(a.get("text", "")), ensure_ascii=False)}

def _json_unescape_string(a):
    value = json.loads(str(a.get("json_string", "")))
    if not isinstance(value, str): raise ValueError("input must be a JSON string literal")
    return {"text": value}

def _json_array_filter(a):
    rows = a.get("items", a.get("json", []))
    if isinstance(rows, str): rows = json.loads(rows)
    if not isinstance(rows, list): raise ValueError("input must be a JSON array")
    key, wanted = str(a.get("key", "")), a.get("equals")
    selected = [row for row in rows if isinstance(row, dict) and str(row.get(key)) == str(wanted)]
    return {"items": selected, "matched": len(selected), "total": len(rows)}

def _json_array_project(a):
    rows, fields = a.get("items", []), a.get("fields", [])
    if isinstance(rows, str): rows = json.loads(rows)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("items must be an array of JSON objects")
    if not fields: raise ValueError("fields are required")
    result = [{key: row.get(key) for key in fields} for row in rows]
    return {"items": result, "count": len(result)}

def _json_diff(a):
    left, right = a.get("before"), a.get("after")
    if isinstance(left, str): left = json.loads(left)
    if isinstance(right, str): right = json.loads(right)
    ltxt = json.dumps(left, ensure_ascii=False, indent=2, sort_keys=True).splitlines(True)
    rtxt = json.dumps(right, ensure_ascii=False, indent=2, sort_keys=True).splitlines(True)
    return {"diff": "".join(difflib.unified_diff(ltxt, rtxt, fromfile="before", tofile="after"))}

def _csv_to_markdown(a):
    reader = csv.reader(io.StringIO(str(a.get("csv", ""))))
    rows = list(reader)
    if not rows: return {"markdown": "", "rows": 0}
    escaped = [[cell.replace("|", "\\|").replace("\n", " ") for cell in row] for row in rows]
    width = len(escaped[0])
    if any(len(row) != width for row in escaped): raise ValueError("CSV rows have inconsistent column counts")
    lines = ["| " + " | ".join(escaped[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped[1:])
    return {"markdown": "\n".join(lines), "rows": len(rows) - 1}

def _csv_merge(a):
    first, second = csv.DictReader(io.StringIO(str(a.get("first", "")))), csv.DictReader(io.StringIO(str(a.get("second", ""))))
    fields = first.fieldnames or []
    if fields != (second.fieldnames or []): raise ValueError("CSV headers must match exactly")
    rows = list(first) + list(second)
    output = io.StringIO()
    if fields:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    return {"csv": output.getvalue(), "rows": len(rows)}

def _csv_unique_count(a):
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    rows, column = list(reader), str(a.get("column", ""))
    if column not in (reader.fieldnames or []): raise ValueError("column not found")
    counts = {}
    for row in rows:
        value = row.get(column, "")
        counts[value] = counts.get(value, 0) + 1
    return {"unique": len(counts), "counts": counts}

def _csv_sample(a):
    import random
    reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
    fields, rows = reader.fieldnames or [], list(reader)
    count = max(0, min(int(a.get("count", 5)), len(rows)))
    indices = sorted(random.Random(int(a.get("seed", 0))).sample(range(len(rows)), count))
    output = io.StringIO()
    if fields:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows[i] for i in indices)
    return {"csv": output.getvalue(), "sampled": count, "total": len(rows)}

def _number_standard_deviation(a):
    import statistics
    values = [float(x) for x in a.get("values", [])]
    sample = bool(a.get("sample", False))
    if len(values) < (2 if sample else 1): raise ValueError("not enough values")
    return {"standard_deviation": statistics.stdev(values) if sample else statistics.pstdev(values),
            "sample": sample, "count": len(values)}

def _number_mode(a):
    from collections import Counter
    values = [float(x) for x in a.get("values", [])]
    if not values: raise ValueError("at least one number is required")
    counts = Counter(values); maximum = max(counts.values())
    return {"modes": sorted(value for value, count in counts.items() if count == maximum),
            "frequency": maximum, "unique_values": len(counts)}

def _number_round(a):
    places = max(-12, min(int(a.get("places", 2)), 12))
    value = float(a.get("value", 0))
    return {"value": round(value, places), "places": places}

def _number_clamp(a):
    value, low, high = float(a.get("value", 0)), float(a.get("minimum", 0)), float(a.get("maximum", 1))
    if low > high: raise ValueError("minimum cannot exceed maximum")
    return {"value": max(low, min(high, value)), "clamped": value < low or value > high}

def _number_factorial(a):
    value = int(a.get("value", 0))
    if not 0 <= value <= 1000: raise ValueError("value must be an integer from 0 to 1000")
    return {"value": value, "factorial": math.factorial(value)}

def _number_prime(a):
    value = int(a.get("value", 0))
    if value < 2: return {"value": value, "prime": False}
    prime = all(value % divisor for divisor in range(2, math.isqrt(value) + 1))
    return {"value": value, "prime": prime}

def _number_range(a):
    start, stop, step = int(a.get("start", 0)), int(a.get("stop", 10)), int(a.get("step", 1))
    if step == 0: raise ValueError("step cannot be zero")
    values = list(range(start, stop, step))
    if len(values) > 10000: raise ValueError("range exceeds 10000 values")
    return {"values": values, "count": len(values)}

def _number_base_convert(a):
    value, base = int(a.get("value", 0)), int(a.get("base", 2))
    if not 2 <= base <= 36: raise ValueError("base must be between 2 and 36")
    alphabet, number = "0123456789abcdefghijklmnopqrstuvwxyz", abs(value)
    if number == 0: result = "0"
    else:
        digits = []
        while number:
            number, remainder = divmod(number, base); digits.append(alphabet[remainder])
        result = "".join(reversed(digits))
    return {"value": value, "base": base, "converted": ("-" if value < 0 else "") + result}

def _percentage_calc(a):
    value, percent = float(a.get("value", 0)), float(a.get("percent", 0))
    return {"value": value, "percent": percent, "result": value * percent / 100}

def _unit_convert(a):
    value, source, target = float(a.get("value", 0)), str(a.get("from", "" )).lower(), str(a.get("to", "")).lower()
    length = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "in": 0.0254, "ft": 0.3048}
    if source in length and target in length:
        result = value * length[source] / length[target]
    elif source in {"c", "f"} and target in {"c", "f"}:
        result = value if source == target else value * 9 / 5 + 32 if source == "c" else (value - 32) * 5 / 9
    else: raise ValueError("supported units: mm, cm, m, km, in, ft, c, f")
    return {"value": result, "from": source, "to": target}

def _color_hex_rgb(a):
    raw = str(a.get("hex", "")).lstrip("#")
    if len(raw) == 3: raw = "".join(ch * 2 for ch in raw)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", raw): raise ValueError("color must be #RGB or #RRGGBB")
    return {"r": int(raw[0:2],16), "g": int(raw[2:4],16), "b": int(raw[4:6],16)}

def _color_rgb_hex(a):
    values = [int(a.get(key, 0)) for key in ("r", "g", "b")]
    if any(v < 0 or v > 255 for v in values): raise ValueError("RGB channels must be from 0 to 255")
    return {"hex": "#" + "".join(f"{v:02X}" for v in values)}

def _ip_cidr_inspect(a):
    import ipaddress
    network = ipaddress.ip_network(str(a.get("cidr", "")), strict=False)
    return {"network": str(network), "version": network.version, "prefix": network.prefixlen,
            "num_addresses": network.num_addresses, "first": str(network.network_address),
            "last": str(network.broadcast_address)}

def _date_weekday(a):
    value = datetime.fromisoformat(str(a.get("date", ""))).date()
    return {"date": value.isoformat(), "weekday": value.strftime("%A"), "weekday_number": value.weekday()}

def _date_add_days(a):
    from datetime import date, timedelta
    value = date.fromisoformat(str(a.get("date", "")))
    result = value + timedelta(days=int(a.get("days", 0)))
    return {"date": value.isoformat(), "days": int(a.get("days", 0)), "result": result.isoformat()}

def _date_diff(a):
    from datetime import date
    first = date.fromisoformat(str(a.get("first", "")))
    second = date.fromisoformat(str(a.get("second", "")))
    return {"days": (second - first).days, "first": first.isoformat(), "second": second.isoformat()}


def _run_extension_task(task, a):
    if task == "text-extract-emails":
        values = re.findall(r"[\w.+-]+@[\w.-]+\.\w{2,}", str(a.get("text", "")))
        return {"matches": values, "count": len(values)}
    if task == "text-extract-urls":
        values = re.findall(r"https?://[^\s<>\"']+", str(a.get("text", "")))
        return {"matches": values, "count": len(values)}
    if task == "text-extract-hashtags":
        values = re.findall(r"(?<!\w)#[\w]+", str(a.get("text", "")))
        return {"hashtags": values, "count": len(values)}
    if task == "text-extract-mentions":
        values = re.findall(r"(?<!\w)@[A-Za-z0-9_]{1,30}", str(a.get("text", "")))
        return {"mentions": values, "count": len(values)}
    if task == "text-extract-phones":
        values = re.findall(r"(?<!\w)\+?\d[\d ().-]{6,}\d(?!\w)", str(a.get("text", "")))
        return {"candidates": values, "count": len(values), "note": "Pattern matches are not verified phone numbers."}
    if task == "text-find-replace":
        text, find = str(a.get("text", "")), str(a.get("find", ""))
        if not find: raise ValueError("find cannot be empty")
        return {"text": text.replace(find, str(a.get("replace", ""))), "replacements": text.count(find)}
    if task == "text-nonempty-lines":
        lines = [line for line in str(a.get("text", "")).splitlines() if line.strip()]
        return {"lines": lines, "count": len(lines)}
    if task == "text-common-prefix":
        left, right = str(a.get("left", "")), str(a.get("right", ""))
        i = 0
        while i < min(len(left), len(right)) and left[i] == right[i]: i += 1
        return {"prefix": left[:i], "length": i}
    if task == "text-common-suffix":
        left, right = str(a.get("left", "")), str(a.get("right", ""))
        i = 0
        while i < min(len(left), len(right)) and left[-i-1] == right[-i-1]: i += 1
        return {"suffix": left[len(left)-i:] if i else "", "length": i}
    if task == "text-word-count":
        words = str(a.get("text", "")).split()
        return {"words": len(words), "characters": len(str(a.get("text", ""))), "unique": len({w.casefold() for w in words})}
    if task == "text-paragraph-count":
        parts = [p for p in re.split(r"\n\s*\n", str(a.get("text", "")).strip()) if p.strip()]
        return {"paragraphs": len(parts), "lengths": [len(p) for p in parts]}
    if task == "text-title-case":
        return {"text": str(a.get("text", "")).title()}
    if task == "text-similarity":
        ratio = difflib.SequenceMatcher(None, str(a.get("left", "")), str(a.get("right", ""))).ratio()
        return {"ratio": ratio, "percent": round(ratio * 100, 2)}
    if task == "text-quote-csv":
        output = io.StringIO()
        csv.writer(output, lineterminator="").writerow([str(a.get("text", ""))])
        return {"csv_field": output.getvalue()}
    if task == "markdown-checklist":
        items = []
        for line in str(a.get("markdown", a.get("text", ""))).splitlines():
            match = re.match(r"^\s*[-*+]\s+\[([ xX])\]\s+(.+)$", line)
            if match: items.append({"checked": match.group(1).lower() == "x", "text": match.group(2).strip()})
        return {"items": items, "checked": sum(item["checked"] for item in items), "total": len(items)}
    if task == "markdown-frontmatter":
        source = str(a.get("markdown", a.get("text", ""))); lines = source.splitlines()
        if not lines or lines[0].strip() != "---": return {"metadata": {}, "body": source}
        try: end = lines.index("---", 1)
        except ValueError: raise ValueError("front matter closing --- not found")
        metadata = {}
        for line in lines[1:end]:
            if ":" in line:
                key, value = line.split(":", 1); metadata[key.strip()] = value.strip().strip("\"'")
        return {"metadata": metadata, "body": "\n".join(lines[end+1:])}
    if task == "markdown-heading-levels":
        items = []
        for number, line in enumerate(str(a.get("markdown", a.get("text", ""))).splitlines(), 1):
            match = re.match(r"^\s*(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if match: items.append({"level": len(match.group(1)), "text": match.group(2), "line": number})
        return {"headings": items, "count": len(items)}
    if task == "json-deep-count":
        obj = a.get("json", a.get("data")); obj = json.loads(obj) if isinstance(obj, str) else obj
        counts = {"objects": 0, "arrays": 0, "keys": 0, "scalars": 0}
        def walk(value):
            if isinstance(value, dict):
                counts["objects"] += 1; counts["keys"] += len(value)
                for item in value.values(): walk(item)
            elif isinstance(value, list):
                counts["arrays"] += 1
                for item in value: walk(item)
            else: counts["scalars"] += 1
        walk(obj); return counts
    if task == "json-array-sort":
        items = a.get("items", a.get("json", [])); items = json.loads(items) if isinstance(items, str) else items
        if not isinstance(items, list): raise ValueError("input must be a JSON array")
        key = str(a.get("key", ""))
        def order(item):
            value = item.get(key) if isinstance(item, dict) and key else item
            return (value is None, str(value).casefold())
        return {"items": sorted(items, key=order, reverse=bool(a.get("reverse", False)))}
    if task == "json-array-dedupe":
        items = a.get("items", a.get("json", [])); items = json.loads(items) if isinstance(items, str) else items
        if not isinstance(items, list): raise ValueError("input must be a JSON array")
        seen, result = set(), []
        for item in items:
            signature = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if signature not in seen: seen.add(signature); result.append(item)
        return {"items": result, "removed": len(items) - len(result)}
    if task == "csv-column-rename":
        reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
        fields, old, new = reader.fieldnames or [], str(a.get("old", "")), str(a.get("new", ""))
        if old not in fields or not new or (new in fields and new != old): raise ValueError("invalid old or new column name")
        new_fields = [new if field == old else field for field in fields]
        output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=new_fields); writer.writeheader()
        for row in reader: row[new] = row.pop(old, ""); writer.writerow(row)
        return {"csv": output.getvalue(), "columns": new_fields}
    if task == "csv-filter-contains":
        reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
        fields, column = reader.fieldnames or [], str(a.get("column", ""))
        if column not in fields: raise ValueError("column not found")
        needle = str(a.get("contains", "")).casefold()
        rows = [row for row in reader if needle in (row.get(column) or "").casefold()]
        output = io.StringIO()
        if fields:
            writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        return {"csv": output.getvalue(), "matched": len(rows)}
    if task == "csv-filter-range":
        reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
        fields, column = reader.fieldnames or [], str(a.get("column", ""))
        if column not in fields: raise ValueError("column not found")
        low, high = float(a.get("minimum", float("-inf"))), float(a.get("maximum", float("inf")))
        if low > high: raise ValueError("minimum cannot exceed maximum")
        rows = []
        for row in reader:
            try: value = float(row.get(column, ""))
            except (TypeError, ValueError): continue
            if low <= value <= high: rows.append(row)
        output = io.StringIO()
        if fields:
            writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        return {"csv": output.getvalue(), "matched": len(rows)}
    if task == "csv-pivot":
        reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
        rows, fields = list(reader), reader.fieldnames or []
        group, value, agg = str(a.get("group_by", "")), str(a.get("value_column", "")), str(a.get("aggregate", "count"))
        if group not in fields: raise ValueError("group_by column not found")
        if agg == "sum" and value not in fields: raise ValueError("value_column not found")
        if agg not in {"count", "sum"}: raise ValueError("aggregate must be count or sum")
        result = {}
        for row in rows:
            key = row.get(group, ""); bucket = result.setdefault(key, {"count": 0, "sum": 0.0}); bucket["count"] += 1
            if agg == "sum":
                try: bucket["sum"] += float(row.get(value, 0) or 0)
                except ValueError: raise ValueError("sum column must contain numbers")
        return {"groups": [{"key": key, **data} for key, data in result.items()], "aggregate": agg}
    if task == "csv-validate":
        reader = csv.DictReader(io.StringIO(str(a.get("csv", ""))))
        fields, rows = reader.fieldnames or [], list(reader); required = [v.strip() for v in a.get("required", [])]
        missing_headers = [key for key in required if key not in fields]
        missing_values = [{"row": i+1, "column": key} for i, row in enumerate(rows)
                          for key in required if key in fields and not (row.get(key) or "").strip()]
        return {"valid": not missing_headers and not missing_values, "missing_headers": missing_headers,
                "missing_values": missing_values, "rows": len(rows)}
    raise KeyError("unknown extension task: " + task)


def _make_extension_handler(task):
    def handler(arguments):
        return _run_extension_task(task, arguments)
    return handler


def _run_dev_extension(task, a, context):
    if task == "python-ast-summary":
        tree = ast.parse(str(a.get("source", "")))
        return {"top_level_nodes": len(tree.body),
                "functions": sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)),
                "classes": sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)),
                "imports": sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))}
    if task == "python-imports":
        tree = ast.parse(str(a.get("source", "")))
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.append(node.module or "")
        found = list(dict.fromkeys(found))
        return {"imports": found, "count": len(found)}
    if task == "python-functions":
        tree = ast.parse(str(a.get("source", "")))
        found = [{"name": n.name, "line": n.lineno, "async": isinstance(n, ast.AsyncFunctionDef)}
                 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        return {"functions": found}
    if task == "python-classes":
        tree = ast.parse(str(a.get("source", "")))
        found = [{"name": n.name, "line": n.lineno,
                  "methods": [x.name for x in n.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]}
                 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        return {"classes": found}
    if task == "lua-functions":
        source = str(a.get("source", ""))
        found = [{"name": m.group(1), "line": source.count("\n", 0, m.start()) + 1}
                 for m in re.finditer(r"\bfunction\s+([A-Za-z_][\w.:]*)", source)]
        return {"functions": found, "count": len(found)}
    if task == "lua-requires":
        source = str(a.get("source", ""))
        found = list(dict.fromkeys(re.findall(r"\brequire\s*\(?\s*['\"]([^'\"]+)['\"]\s*\)?", source)))
        return {"modules": found, "count": len(found)}
    if task == "js-imports":
        source = str(a.get("source", ""))
        found = re.findall(r"(?:import\s+(?:[^'\"]+?\s+from\s+)?|require\s*\()\s*['\"]([^'\"]+)['\"]", source)
        return {"imports": found, "count": len(found)}
    if task == "js-functions":
        source = str(a.get("source", ""))
        names = re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", source)
        names += re.findall(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", source)
        names = list(dict.fromkeys(names))
        return {"functions": names, "count": len(names)}
    if task == "html-meta-extract":
        source = str(a.get("html", ""))
        metas = []
        for tag in re.findall(r"(?is)<meta\b[^>]*>", source):
            name = re.search(r"(?i)(?:name|property)\s*=\s*['\"]([^'\"]+)", tag)
            content = re.search(r"(?i)content\s*=\s*['\"]([^'\"]*)", tag)
            if name and content:
                metas.append({"name": name.group(1), "content": html.unescape(content.group(1))})
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", source)
        return {"title": html.unescape(title.group(1).strip()) if title else "", "meta": metas}
    if task == "xml-format":
        from xml.dom import minidom
        document = minidom.parseString(str(a.get("xml", "")))
        return {"xml": document.toprettyxml(indent="  ")}
    if task == "log-level-count":
        text = str(a.get("text", ""))
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        counts = {level: len(re.findall(r"\b" + level + r"\b", text, flags=re.I)) for level in levels}
        return {"counts": counts, "total": sum(counts.values())}
    if task == "traceback-summary":
        text = str(a.get("traceback", a.get("text", "")))
        last = next((line.strip() for line in reversed(text.splitlines()) if line.strip()), "")
        frames = [{"file": m.group(1), "line": int(m.group(2))}
                  for m in re.finditer(r'File "([^"]+)", line (\d+)', text)]
        error = re.search(r"([A-Za-z_][A-Za-z0-9]*Error|Exception):\s*(.*)$", last)
        return {"last_line": last, "exception": error.group(1) if error else None,
                "message": error.group(2) if error else "", "frames": frames}
    if task == "git-diff-stats":
        lines = str(a.get("diff", "")).splitlines()
        added = sum(line.startswith("+") and not line.startswith("+++") for line in lines)
        removed = sum(line.startswith("-") and not line.startswith("---") for line in lines)
        files = [line[11:] for line in lines if line.startswith("diff --git ")]
        return {"files": files, "added": added, "removed": removed}
    if task == "semver-normalize":
        raw = str(a.get("version", "")).strip()
        match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", raw)
        if not match:
            raise ValueError("version must be MAJOR.MINOR.PATCH without prerelease")
        return {"version": ".".join(str(int(part)) for part in match.groups())}
    if task == "semver-sort":
        versions = [str(value).strip() for value in a.get("versions", [])]
        def parse(value):
            match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
            if not match:
                raise ValueError("all versions must be MAJOR.MINOR.PATCH")
            return tuple(map(int, match.groups()))
        return {"versions": sorted(versions, key=parse), "count": len(versions)}
    if task == "duration-parse":
        raw = str(a.get("value", ""))
        parts = raw.split(":")
        if not 2 <= len(parts) <= 3 or any(not part.isdigit() for part in parts):
            raise ValueError("use MM:SS or HH:MM:SS")
        numbers = list(map(int, parts))
        if any(value >= 60 for value in numbers[1:]):
            raise ValueError("minutes and seconds must be below 60")
        seconds = numbers[-1] + numbers[-2] * 60 + (numbers[-3] * 3600 if len(numbers) == 3 else 0)
        return {"seconds": seconds, "duration": raw}
    if task == "image-dimensions":
        context.require("filesystem.read")
        path = Path(str(a.get("path", ""))).expanduser().resolve()
        data = path.read_bytes()[:4000000]
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            width = int.from_bytes(data[16:20], "big")
            height = int.from_bytes(data[20:24], "big")
        elif data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 10:
            width = int.from_bytes(data[6:8], "little")
            height = int.from_bytes(data[8:10], "little")
        else:
            raise ValueError("unsupported or invalid PNG or GIF file")
        if not width or not height:
            raise ValueError("image dimensions must be positive")
        return {"path": str(path), "width": width, "height": height,
                "aspect_ratio": round(width / height, 4)}
    if task == "file-checksum":
        context.require("filesystem.read")
        path = Path(str(a.get("path", ""))).expanduser().resolve()
        algorithm = str(a.get("algorithm", "sha256")).lower()
        if algorithm not in hashlib.algorithms_guaranteed:
            raise ValueError("unsupported hash algorithm")
        digest = hashlib.new(algorithm)
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return {"path": str(path), "algorithm": algorithm, "digest": digest.hexdigest()}
    if task == "directory-size":
        context.require("filesystem.read")
        root = Path(str(a.get("path", "."))).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("path is not a directory")
        limit = max(1, min(int(a.get("max_files", 10000)), 100000))
        total = count = 0
        for item in root.rglob("*"):
            if item.is_file() and not item.is_symlink():
                total += item.stat().st_size
                count += 1
                if count >= limit:
                    break
        return {"path": str(root), "bytes": total, "files_scanned": count, "limit": limit}
    if task == "file-size-human":
        context.require("filesystem.read")
        path = Path(str(a.get("path", ""))).expanduser().resolve()
        size = path.stat().st_size
        value, unit = float(size), "B"
        for candidate in ["KB", "MB", "GB", "TB"]:
            if value < 1024:
                break
            value /= 1024
            unit = candidate
        return {"path": str(path), "bytes": size, "human": f"{value:.2f} {unit}"}
    if task == "file-mime-guess":
        import mimetypes
        name = str(a.get("filename", ""))
        mime, encoding = mimetypes.guess_type(name)
        return {"filename": name, "mime_type": mime, "encoding": encoding}
    if task == "file-name-sanitize":
        name = str(a.get("name", ""))
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
        return {"filename": cleaned[:180]}
    if task == "path-extension":
        from pathlib import PurePath
        name = str(a.get("path", ""))
        path = PurePath(name)
        return {"name": path.name, "stem": path.stem, "suffix": path.suffix.lower()}
    if task == "code-fence-extract":
        source = str(a.get("markdown", a.get("text", "")))
        fence = chr(96) * 3
        pattern = re.escape(fence) + r"([^\n]*)\n(.*?)" + re.escape(fence)
        blocks = [{"language": (m.group(1) or "").strip(), "code": m.group(2)}
                  for m in re.finditer(pattern, source, flags=re.S)]
        return {"blocks": blocks, "count": len(blocks)}
    if task == "markdown-word-count":
        text = re.sub(r"(?m)^\s*#+\s*", "", str(a.get("markdown", a.get("text", ""))))
        words = re.findall(r"\b[\w']+\b", text)
        return {"words": len(words), "characters": len(text)}
    raise KeyError("unknown developer extension task: " + task)


def _make_dev_extension_handler(task):
    def handler(arguments, context=None):
        return _run_dev_extension(task, arguments, context)
    return handler


def _run_data_extension(task, a, context):
    if task == "json-path-set":
        import copy
        value = a.get("json", a.get("data"))
        if isinstance(value, str): value = json.loads(value)
        if not isinstance(value, dict): raise ValueError("input must be a JSON object")
        result = copy.deepcopy(value)
        keys = [part for part in str(a.get("path", "")).split(".") if part]
        if not keys: raise ValueError("path is required")
        current = result
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict): raise ValueError("intermediate path must exist")
            current = current[key]
        current[keys[-1]] = a.get("value")
        return {"data": result}
    if task == "json-to-xml":
        value = a.get("json", a.get("data"))
        if isinstance(value, str): value = json.loads(value)
        def add(parent, name, item):
            node = ET.SubElement(parent, str(name))
            if isinstance(item, dict):
                for key, child in item.items(): add(node, key, child)
            elif isinstance(item, list):
                for child in item: add(node, "item", child)
            elif item is not None:
                node.text = str(item).lower() if isinstance(item, bool) else str(item)
        root = ET.Element("root")
        if isinstance(value, dict):
            for key, item in value.items(): add(root, key, item)
        else: add(root, "item", value)
        return {"xml": ET.tostring(root, encoding="unicode")}
    if task == "xml-to-json":
        root = ET.fromstring(str(a.get("xml", "")))
        def convert(node):
            if not list(node): return node.text or ""
            result = {}
            for child in list(node):
                value = convert(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list): result[child.tag] = [result[child.tag]]
                    result[child.tag].append(value)
                else: result[child.tag] = value
            return result
        return {"root": root.tag, "data": convert(root)}
    if task == "html-heading-outline":
        source = str(a.get("html", ""))
        items = []
        for match in re.finditer(r"(?is)<h([1-6])\b[^>]*>(.*?)</h\1>", source):
            text = re.sub(r"(?s)<[^>]+>", " ", match.group(2))
            items.append({"level": int(match.group(1)), "text": re.sub(r"\s+", " ", html.unescape(text)).strip()})
        return {"headings": items, "count": len(items)}
    if task == "html-image-extract":
        images = []
        for tag in re.findall(r"(?is)<img\b[^>]*>", str(a.get("html", ""))):
            src = re.search(r"(?i)\bsrc\s*=\s*['\"]([^'\"]*)", tag)
            alt = re.search(r"(?i)\balt\s*=\s*['\"]([^'\"]*)", tag)
            images.append({"src": html.unescape(src.group(1)) if src else "", "alt": html.unescape(alt.group(1)) if alt else ""})
        return {"images": images, "count": len(images)}
    if task == "http-header-parse":
        headers = {}
        for line in str(a.get("text", "")).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                headers.setdefault(key.strip().lower(), []).append(value.strip())
        return {"headers": headers, "count": len(headers)}
    if task == "url-build":
        from urllib.parse import urlencode, urlsplit, urlunsplit
        parts = urlsplit(str(a.get("base_url", "")))
        params = a.get("params", {})
        if not isinstance(params, dict): raise ValueError("params must be an object")
        return {"url": urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params, doseq=True), parts.fragment))}
    if task == "email-validate":
        email = str(a.get("email", "")).strip()
        valid = bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email))
        return {"email": email, "valid_format": valid, "note": "Mailbox existence is not verified."}
    if task == "phone-normalize":
        value = str(a.get("phone", ""))
        digits = re.sub(r"\D", "", value)
        return {"normalized": ("+" if value.strip().startswith("+") else "") + digits, "digit_count": len(digits)}
    if task == "password-strength":
        value = str(a.get("password", ""))
        groups = sum(bool(re.search(pattern, value)) for pattern in [r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"])
        score = min(4, int(len(value) >= 8) + int(len(value) >= 12) + int(len(value) >= 16) + int(groups >= 3))
        return {"score": score, "label": ["very weak","weak","fair","strong","very strong"][score],
                "length": len(value), "note": "Heuristic only; password is not stored."}
    if task == "random-string":
        import secrets, string
        length = max(1, min(int(a.get("length", 16)), 256))
        alphabet = str(a.get("alphabet", string.ascii_letters + string.digits))
        if len(set(alphabet)) < 2: raise ValueError("alphabet needs at least two distinct characters")
        return {"value": "".join(secrets.choice(alphabet) for _ in range(length)), "length": length}
    if task == "lorem-generate":
        words = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua".split()
        count = max(1, min(int(a.get("words", 50)), 2000))
        text = " ".join(words[index % len(words)] for index in range(count))
        paragraphs = max(1, min(int(a.get("paragraphs", 1)), 20))
        result = []
        for index in range(paragraphs):
            chunk = " ".join(text.split()[index::paragraphs]) if paragraphs > 1 else text
            result.append(chunk[:1].upper() + chunk[1:] + ".")
        return {"text": "\n\n".join(result), "paragraphs": paragraphs}
    if task == "uuid-parse":
        value = uuid.UUID(str(a.get("uuid", "")))
        return {"canonical": str(value), "version": value.version, "variant": value.variant}
    if task == "timestamp-convert":
        value = a.get("value")
        if isinstance(value, (int, float)):
            moment = datetime.fromtimestamp(float(value), tz=timezone.utc)
        else:
            moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if moment.tzinfo is None: moment = moment.replace(tzinfo=timezone.utc)
        return {"unix": moment.timestamp(), "utc": moment.astimezone(timezone.utc).isoformat()}
    if task == "timezone-convert":
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        moment = datetime.fromisoformat(str(a.get("value", "")).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=ZoneInfo(str(a.get("from_zone", "UTC"))))
        try: converted = moment.astimezone(ZoneInfo(str(a.get("to_zone", "UTC"))))
        except ZoneInfoNotFoundError as exc: raise ValueError("unknown timezone") from exc
        return {"source": moment.isoformat(), "converted": converted.isoformat()}
    if task == "file-find":
        context.require("filesystem.read")
        root = Path(str(a.get("path", "."))).expanduser().resolve()
        if not root.is_dir(): raise ValueError("path is not a directory")
        pattern = str(a.get("pattern", "*"))
        limit = max(1, min(int(a.get("limit", 100)), 2000))
        found = [p for p in (root.rglob(pattern) if a.get("recursive") else root.glob(pattern)) if not p.is_symlink()]
        return {"matches": [{"path": str(p), "is_dir": p.is_dir(), "size": p.stat().st_size if p.is_file() else None} for p in found[:limit]],
                "count": min(len(found), limit), "truncated": len(found) > limit}
    if task == "file-text-search":
        context.require("filesystem.read")
        root = Path(str(a.get("path", "."))).expanduser().resolve()
        needle = str(a.get("query", ""))
        if not root.is_dir() or not needle: raise ValueError("directory and query are required")
        hits = []
        scanned = 0
        for path in root.rglob("*"):
            if not path.is_file() or path.is_symlink() or path.stat().st_size > 1000000: continue
            scanned += 1
            try: lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError): continue
            for number, line in enumerate(lines, 1):
                if needle.casefold() in line.casefold(): hits.append({"path": str(path), "line": number, "text": line[:500]})
            if scanned >= max(1, min(int(a.get("max_files", 1000)), 5000)): break
        return {"matches": hits[:500], "count": min(len(hits), 500), "files_scanned": scanned}
    if task == "duplicate-files":
        context.require("filesystem.read")
        root = Path(str(a.get("path", "."))).expanduser().resolve()
        if not root.is_dir(): raise ValueError("path is not a directory")
        groups, scanned = {}, 0
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                groups.setdefault(path.stat().st_size, []).append(path)
                scanned += 1
                if scanned >= max(1, min(int(a.get("max_files", 2000)), 10000)): break
        duplicates = []
        for size, paths in groups.items():
            if len(paths) < 2: continue
            by_hash = {}
            for path in paths:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                by_hash.setdefault(digest, []).append(str(path))
            for digest, names in by_hash.items():
                if len(names) > 1: duplicates.append({"sha256": digest, "size": size, "paths": names})
        return {"groups": duplicates, "files_scanned": scanned}
    if task == "directory-tree":
        context.require("filesystem.read")
        root = Path(str(a.get("path", "."))).expanduser().resolve()
        if not root.is_dir(): raise ValueError("path is not a directory")
        max_depth = max(0, min(int(a.get("max_depth", 3)), 10))
        limit = max(1, min(int(a.get("max_entries", 300)), 2000))
        entries = []
        def walk(folder, depth):
            if depth > max_depth or len(entries) >= limit: return
            children = sorted(folder.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold()))
            for child in children:
                if child.is_symlink() or len(entries) >= limit: continue
                entries.append({"path": str(child.relative_to(root)), "directory": child.is_dir(), "depth": depth})
                if child.is_dir(): walk(child, depth + 1)
        walk(root, 0)
        return {"root": str(root), "entries": entries, "truncated": len(entries) >= limit}
    if task == "file-extension-count":
        context.require("filesystem.read")
        root = Path(str(a.get("path", "."))).expanduser().resolve()
        if not root.is_dir(): raise ValueError("path is not a directory")
        counts = {}
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                suffix = path.suffix.lower() or "[no extension]"
                counts[suffix] = counts.get(suffix, 0) + 1
        return {"extensions": counts, "files": sum(counts.values())}
    if task == "xml-attrs-extract":
        root = ET.fromstring(str(a.get("xml", "")))
        values = [{"tag": node.tag, "attributes": dict(node.attrib)} for node in root.iter() if node.attrib]
        return {"elements": values, "count": len(values)}
    if task == "css-colors-extract":
        values = re.findall(r"#[0-9a-fA-F]{3,8}\b", str(a.get("css", "")))
        values = list(dict.fromkeys(values))
        return {"colors": values, "count": len(values)}
    if task == "css-rule-count":
        source = re.sub(r"/\*.*?\*/", "", str(a.get("css", "")), flags=re.S)
        rules = re.findall(r"([^{}]+)\{([^{}]*)\}", source)
        selectors = [selector.strip() for selector, body in rules if selector.strip()]
        count = sum(len([part for part in body.split(";") if ":" in part]) for selector, body in rules)
        return {"rules": len(selectors), "selectors": selectors, "declarations": count}
    if task == "html-form-inspect":
        source = str(a.get("html", ""))
        forms = []
        for attrs, body in re.findall(r"(?is)<form\b([^>]*)>(.*?)</form>", source):
            action = re.search(r"(?i)\baction\s*=\s*['\"]([^'\"]*)", attrs)
            method = re.search(r"(?i)\bmethod\s*=\s*['\"]([^'\"]*)", attrs)
            fields = []
            for tag in re.findall(r"(?is)<(?:input|select|textarea)\b[^>]*>", body):
                name = re.search(r"(?i)\bname\s*=\s*['\"]([^'\"]*)", tag)
                kind = re.search(r"(?i)\btype\s*=\s*['\"]([^'\"]*)", tag)
                if name: fields.append({"name": name.group(1), "type": kind.group(1) if kind else "text"})
            forms.append({"action": action.group(1) if action else "",
                          "method": method.group(1).upper() if method else "GET", "fields": fields})
        return {"forms": forms, "count": len(forms)}
    if task == "html-table-extract":
        source = str(a.get("html", ""))
        tables = []
        for table in re.findall(r"(?is)<table\b[^>]*>(.*?)</table>", source):
            rows = []
            for row in re.findall(r"(?is)<tr\b[^>]*>(.*?)</tr>", table):
                cells = []
                for cell in re.findall(r"(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>", row):
                    text = re.sub(r"(?s)<[^>]+>", " ", cell)
                    cells.append(re.sub(r"\s+", " ", html.unescape(text)).strip())
                if cells: rows.append(cells)
            tables.append(rows)
        return {"tables": tables, "count": len(tables)}
    raise KeyError("unknown data extension task: " + task)


def _make_data_extension_handler(task):
    def handler(arguments, context=None):
        return _run_data_extension(task, arguments, context)
    return handler


def _run_final_extension(task, a, context):
    if task == "file-line-count":
        context.require("filesystem.read")
        path = Path(str(a.get("path", ""))).expanduser().resolve()
        if path.stat().st_size > 5000000: raise ValueError("file exceeds the 5 MB text limit")
        text = path.read_text(encoding="utf-8")
        return {"path": str(path), "lines": len(text.splitlines()), "characters": len(text)}
    if task in {"file-head", "file-tail"}:
        context.require("filesystem.read")
        path = Path(str(a.get("path", ""))).expanduser().resolve()
        if path.stat().st_size > 5000000: raise ValueError("file exceeds the 5 MB text limit")
        lines = path.read_text(encoding="utf-8").splitlines()
        count = max(0, min(int(a.get("lines", 10)), 1000))
        selected = lines[:count] if task == "file-head" else (lines[-count:] if count else [])
        return {"path": str(path), "lines": selected, "returned": len(selected), "total_lines": len(lines)}
    if task == "file-json-inspect":
        context.require("filesystem.read")
        path = Path(str(a.get("path", ""))).expanduser().resolve()
        if path.stat().st_size > 2000000: raise ValueError("JSON file exceeds the 2 MB limit")
        value = json.loads(path.read_text(encoding="utf-8"))
        return {"path": str(path), "type": "object" if isinstance(value, dict) else "array" if isinstance(value, list) else type(value).__name__,
                "keys": list(value) if isinstance(value, dict) else [], "items": len(value) if isinstance(value, (dict, list)) else None}
    if task == "archive-create":
        context.require("filesystem.write")
        destination = Path(str(a.get("path", ""))).expanduser().resolve()
        files = a.get("files", {})
        if not destination.name or not isinstance(files, dict): raise ValueError("path and files mapping are required")
        if destination.exists(): raise FileExistsError(str(destination))
        from pathlib import PurePosixPath
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                member = PurePosixPath(str(name))
                if member.is_absolute() or ".." in member.parts or not member.parts:
                    raise ValueError("unsafe archive entry path")
                archive.writestr(str(member), str(content))
        return {"path": str(destination), "entries": len(files), "bytes": destination.stat().st_size}
    if task == "archive-extract-safe":
        context.require("filesystem.read")
        context.require("filesystem.write")
        source = Path(str(a.get("archive", ""))).expanduser().resolve()
        destination = Path(str(a.get("destination", ""))).expanduser().resolve()
        if not source.is_file(): raise ValueError("archive file not found")
        destination.mkdir(parents=True, exist_ok=True)
        total = 0
        extracted = []
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if len(infos) > 1000: raise ValueError("archive contains too many entries")
            for info in infos:
                member = Path(info.filename)
                target = (destination / member).resolve()
                if member.is_absolute() or ".." in member.parts or (target != destination and destination not in target.parents):
                    raise ValueError("unsafe archive entry path")
                total += info.file_size
                if total > 25000000: raise ValueError("archive expands beyond the 25 MB limit")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(info))
                    extracted.append(str(target))
        return {"destination": str(destination), "files": extracted, "count": len(extracted), "bytes": total}
    if task == "file-copy":
        context.require("filesystem.read")
        context.require("filesystem.write")
        source = Path(str(a.get("source", ""))).expanduser().resolve()
        destination = Path(str(a.get("destination", ""))).expanduser().resolve()
        if not source.is_file(): raise ValueError("source file not found")
        if destination.exists(): raise FileExistsError(str(destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        return {"source": str(source), "destination": str(destination), "bytes": destination.stat().st_size}
    if task == "file-rename":
        context.require("filesystem.write")
        source = Path(str(a.get("path", ""))).expanduser().resolve()
        new_name = str(a.get("new_name", ""))
        if not source.exists() or not new_name or Path(new_name).name != new_name:
            raise ValueError("source must exist and new_name must be a filename only")
        destination = source.with_name(new_name)
        if destination.exists(): raise FileExistsError(str(destination))
        source.rename(destination)
        return {"old_path": str(source), "new_path": str(destination)}
    if task == "directory-empty-check":
        context.require("filesystem.read")
        root = Path(str(a.get("path", ""))).expanduser().resolve()
        if not root.is_dir(): raise ValueError("path is not a directory")
        return {"path": str(root), "empty": next(root.iterdir(), None) is None}
    if task == "json-schema-lite":
        value, schema = a.get("data"), a.get("schema", {})
        if isinstance(value, str): value = json.loads(value)
        if isinstance(schema, str): schema = json.loads(schema)
        if not isinstance(schema, dict): raise ValueError("schema must be an object")
        expected = schema.get("type")
        type_ok = {"object": isinstance(value, dict), "array": isinstance(value, list),
                   "string": isinstance(value, str), "number": isinstance(value, (int, float)) and not isinstance(value, bool),
                   "integer": isinstance(value, int) and not isinstance(value, bool),
                   "boolean": isinstance(value, bool), "null": value is None}
        errors = []
        if expected in type_ok and not type_ok[expected]: errors.append("expected type " + expected)
        if isinstance(value, dict):
            for key in schema.get("required", []):
                if key not in value: errors.append("missing required key: " + str(key))
            for key, rule in schema.get("properties", {}).items():
                if key in value and isinstance(rule, dict) and rule.get("type") in type_ok:
                    if not type_ok[rule["type"]]: errors.append("property " + key + " expected " + rule["type"])
        if isinstance(value, list) and isinstance(schema.get("items"), dict):
            rule = schema["items"]
            if rule.get("type") in type_ok:
                for index, item in enumerate(value):
                    if not type_ok[rule["type"]]: errors.append("item type mismatch")
                    break
        return {"valid": not errors, "errors": errors, "checked_type": expected}
    if task == "json-redact-keys":
        value = a.get("json", a.get("data"))
        if isinstance(value, str): value = json.loads(value)
        keys = {str(key).casefold() for key in a.get("keys", ["password", "secret", "token", "api_key", "access_token"])}
        def redact(item):
            if isinstance(item, dict):
                return {key: "[REDACTED]" if str(key).casefold() in keys else redact(child) for key, child in item.items()}
            if isinstance(item, list): return [redact(child) for child in item]
            return item
        return {"data": redact(value), "redacted_keys": sorted(keys)}
    if task == "xml-element-paths":
        root = ET.fromstring(str(a.get("xml", "")))
        result = []
        def visit(node, path):
            result.append({"path": path, "tag": node.tag, "attributes": dict(node.attrib)})
            counts = {}
            for child in list(node):
                counts[child.tag] = counts.get(child.tag, 0) + 1
                visit(child, path + "/" + child.tag + "[" + str(counts[child.tag]) + "]")
        visit(root, "/" + root.tag + "[1]")
        return {"elements": result, "count": len(result)}
    if task == "text-compare-lines":
        from itertools import zip_longest
        left = str(a.get("left", "")).splitlines()
        right = str(a.get("right", "")).splitlines()
        changes = [{"line": index, "before": first, "after": second}
                   for index, (first, second) in enumerate(zip_longest(left, right), 1) if first != second]
        return {"changes": changes, "changed_lines": len(changes), "same": not changes}
    if task == "todo-extract":
        markers = []
        pattern = re.compile(r"\b(TODO|FIXME|BUG)\b\s*:?\s*(.*)", re.I)
        for number, line in enumerate(str(a.get("text", "")).splitlines(), 1):
            match = pattern.search(line)
            if match: markers.append({"kind": match.group(1).upper(), "line": number, "text": match.group(2).strip()})
        return {"markers": markers, "count": len(markers)}
    if task == "number-gcd-lcm":
        left, right = int(a.get("left", 0)), int(a.get("right", 0))
        gcd = math.gcd(left, right)
        lcm = abs(left * right) // gcd if gcd else 0
        return {"gcd": gcd, "lcm": lcm}
    if task == "number-roman":
        number = int(a.get("value", 0))
        if not 1 <= number <= 3999: raise ValueError("value must be from 1 to 3999")
        pairs = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),(50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
        result = []
        for amount, symbol in pairs:
            count, number = divmod(number, amount)
            result.append(symbol * count)
        return {"roman": "".join(result)}
    if task in {"color-rgb-hsl", "color-hsl-rgb"}:
        import colorsys
        if task == "color-rgb-hsl":
            channels = [float(a.get(key, 0)) / 255 for key in ("r", "g", "b")]
            if any(value < 0 or value > 1 for value in channels): raise ValueError("RGB channels must be 0 to 255")
            h, light, sat = colorsys.rgb_to_hls(*channels)
            return {"h": round(h * 360, 2), "s": round(sat * 100, 2), "l": round(light * 100, 2)}
        h = float(a.get("h", 0)) % 360 / 360
        sat, light = float(a.get("s", 0)) / 100, float(a.get("l", 0)) / 100
        if not 0 <= sat <= 1 or not 0 <= light <= 1: raise ValueError("S and L must be 0 to 100")
        r, g, b = colorsys.hls_to_rgb(h, light, sat)
        return {"r": round(r * 255), "g": round(g * 255), "b": round(b * 255)}
    if task == "date-month-calendar":
        import calendar
        year, month = int(a.get("year", 2026)), int(a.get("month", 1))
        if not 1 <= month <= 12: raise ValueError("month must be 1 to 12")
        return {"year": year, "month": month, "weeks": calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)}
    if task == "date-week-number":
        value = datetime.fromisoformat(str(a.get("date", ""))).date()
        iso = value.isocalendar()
        return {"date": value.isoformat(), "iso_year": iso.year, "week": iso.week, "weekday": iso.weekday}
    if task == "url-safe-check":
        from urllib.parse import urlsplit
        value = str(a.get("url", ""))
        try:
            parts = urlsplit(value)
            valid = parts.scheme in {"http", "https"} and bool(parts.hostname) and not parts.username and not parts.password
            if parts.port is not None and not 1 <= parts.port <= 65535: valid = False
        except ValueError:
            valid = False
        return {"url": value, "valid_http_url": valid}
    if task == "html-link-domain-count":
        from urllib.parse import urlparse
        domains = {}
        for href in re.findall(r"(?is)<a\b[^>]*href\s*=\s*['\"]([^'\"]+)", str(a.get("html", ""))):
            host = urlparse(html.unescape(href)).hostname or "[relative]"
            domains[host.lower()] = domains.get(host.lower(), 0) + 1
        return {"domains": domains, "links": sum(domains.values())}
    if task == "css-variable-extract":
        source = str(a.get("css", ""))
        variables = dict(re.findall(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]+)", source))
        return {"variables": {key: value.strip() for key, value in variables.items()}, "count": len(variables)}
    if task == "jsonl-to-json":
        rows = []
        for number, line in enumerate(str(a.get("text", "")).splitlines(), 1):
            if line.strip():
                try: rows.append(json.loads(line))
                except json.JSONDecodeError as exc: raise ValueError("invalid JSON on line " + str(number)) from exc
        return {"json": json.dumps(rows, ensure_ascii=False, indent=2), "count": len(rows)}
    if task == "json-to-jsonl":
        items = a.get("items", a.get("json", []))
        if isinstance(items, str): items = json.loads(items)
        if not isinstance(items, list): raise ValueError("input must be a JSON array")
        return {"text": "\n".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) for item in items),
                "count": len(items)}
    raise KeyError("unknown final extension task: " + task)


def _make_final_extension_handler(task):
    def handler(arguments, context=None):
        return _run_final_extension(task, arguments, context)
    return handler


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
    ("markdown-toc", "Markdown TOC", "Build a table of contents from Markdown headings.", ["markdown","heading","toc"], _markdown_toc),
    ("markdown-links", "Markdown Link Extractor", "Extract Markdown link labels and destinations.", ["markdown","links","extract"], _markdown_links),
    ("text-dedupe-lines", "Line Deduplicator", "Remove repeated lines and keep their first occurrence.", ["text","dedupe","lines"], _text_dedupe_lines),
    ("text-sort-lines", "Line Sorter", "Sort text lines alphabetically with optional reverse order.", ["text","sort","lines"], _text_sort_lines),
    ("text-case", "Text Case Converter", "Convert text into upper, lower, title, or sentence case.", ["text","case","uppercase"], _text_case),
    ("word-frequency", "Word Frequency", "Count word frequency and return the most common terms.", ["word","frequency","count"], _word_frequency),
    ("html-links", "HTML Link Extractor", "Extract anchor links from HTML source.", ["html","links","href"], _html_links),
    ("json-flatten", "JSON Flattener", "Flatten nested JSON objects and arrays into dotted paths.", ["json","flatten","nested"], _json_flatten),
    ("csv-to-json", "CSV to JSON", "Convert CSV records into a JSON array of objects.", ["csv","json","convert"], _csv_to_json),
    ("toml-parse", "TOML Inspector", "Parse TOML configuration using Python's tomllib.", ["toml","config","parse"], _toml_parse),
    ("markdown-table", "Markdown Table Builder", "Build a Markdown table from headers and rows.", ["markdown","table"], _markdown_table),
    ("markdown-to-text", "Markdown Plain Text", "Convert Markdown source into readable plain text.", ["markdown","plain text"], _markdown_to_text),
    ("text-wrap", "Text Wrapper", "Wrap text paragraphs to a configurable width.", ["text","wrap","format"], _text_wrap),
    ("text-mask-secrets", "Secret Masker", "Mask likely credentials in text before sharing or logging.", ["secret","mask","redact","token"], _text_mask_secrets),
    ("regex-replace", "Regex Replacer", "Replace regex matches with a supplied replacement string.", ["regex","replace","pattern"], _regex_replace),
    ("html-clean", "HTML Cleaner", "Convert HTML source into text while skipping script and style blocks.", ["html","clean","plain text"], _html_clean),
    ("json-merge", "JSON Object Merger", "Merge two JSON objects; right-side keys take precedence.", ["json","merge","combine"], _json_merge),
    ("json-pointer", "JSON Pointer Lookup", "Look up nested JSON values using a slash-separated pointer.", ["json","pointer","lookup"], _json_pointer),
    ("csv-column-select", "CSV Column Selector", "Select and reorder requested CSV columns.", ["csv","columns","select"], _csv_column_select),
    ("csv-sort", "CSV Sorter", "Sort CSV rows by a selected column.", ["csv","sort","rows"], _csv_sort),
    ("csv-dedupe", "CSV Deduplicator", "Remove duplicate CSV rows based on selected columns.", ["csv","dedupe","duplicate"], _csv_dedupe),
    ("ini-parse", "INI Configuration Reader", "Parse INI sections and key-value settings.", ["ini","config","parse"], _ini_parse),
    ("color-contrast", "Color Contrast Checker", "Calculate WCAG contrast ratio between two hexadecimal colors.", ["color","contrast","accessibility"], _color_contrast),
    ("web-fetch", "Public Web Page Reader", "Fetch public HTTP(S) page text; requires network.read and does not run JavaScript.", ["web","fetch","page","http"], _web_fetch),
    ("url-query-parse", "URL Query Parser", "Parse URL query parameters into a structured mapping.", ["url","query","parameters"], _url_query_parse),
    ("text-reverse", "Text Reverser", "Reverse the character order of supplied text.", ["text","reverse"], _text_reverse),
    ("text-sentence-count", "Sentence Counter", "Count sentence-ending punctuation marks in text.", ["text","sentence","count"], _text_sentence_count),
    ("text-char-frequency", "Character Frequency", "Count each character and its frequency.", ["text","character","frequency"], _text_char_frequency),
    ("text-remove-blank", "Blank Line Remover", "Remove empty or whitespace-only lines.", ["text","blank","lines"], _text_remove_blank),
    ("text-indent", "Text Indenter", "Add a chosen indentation prefix to each line.", ["text","indent"], _text_indent),
    ("text-dedent", "Text Dedenter", "Remove common leading indentation from text.", ["text","dedent","indent"], _text_dedent),
    ("text-number-lines", "Line Numberer", "Prefix each line with a configurable line number.", ["text","line numbers"], _text_number_lines),
    ("text-truncate", "Text Truncator", "Limit text length and append a configurable suffix.", ["text","truncate","shorten"], _text_truncate),
    ("text-prefix-lines", "Line Prefixer", "Add a prefix to every non-empty text line.", ["text","prefix","lines"], _text_prefix_lines),
    ("text-suffix-lines", "Line Suffixer", "Add a suffix to every non-empty text line.", ["text","suffix","lines"], _text_suffix_lines),
    ("text-unique-words", "Unique Word Extractor", "Return unique words in first-seen order.", ["text","unique","words"], _text_unique_words),
    ("text-palindrome", "Palindrome Checker", "Check whether text is a palindrome after removing punctuation and spaces.", ["text","palindrome"], _text_palindrome),
    ("text-rot13", "ROT13 Encoder", "Apply the reversible ROT13 text transform.", ["text","rot13","cipher"], _text_rot13),
    ("json-keys", "JSON Key Enumerator", "List keys from a JSON object at the top level.", ["json","keys","object"], _json_keys),
    ("json-values", "JSON Value Enumerator", "Return values from a top-level JSON object.", ["json","values","object"], _json_values),
    ("json-types", "JSON Type Inspector", "Report top-level JSON value types by key.", ["json","types","inspect"], _json_types),
    ("json-array-stats", "JSON Array Statistics", "Summarize item count and value types in a JSON array.", ["json","array","statistics"], _json_array_stats),
    ("json-sort-keys", "JSON Key Sorter", "Sort JSON object keys recursively and format the result.", ["json","sort","keys"], _json_sort_keys),
    ("json-minify", "JSON Minifier", "Serialize valid JSON with compact separators.", ["json","minify","compact"], _json_minify),
    ("csv-column-stats", "CSV Column Statistics", "Count unique, blank, and filled values in one CSV column.", ["csv","column","statistics"], _csv_column_stats),
    ("csv-head", "CSV Head", "Return the first N data rows from CSV while preserving its header.", ["csv","head","preview"], _csv_head),
    ("csv-tail", "CSV Tail", "Return the final N data rows from CSV while preserving its header.", ["csv","tail","preview"], _csv_tail),
    ("csv-transpose", "CSV Transposer", "Transpose CSV rows and columns.", ["csv","transpose","matrix"], _csv_transpose),
    ("number-stats", "Number Statistics", "Calculate count, mean, median, minimum, maximum, and population variance.", ["number","statistics","mean"], _number_stats),
    ("number-percentile", "Percentile Calculator", "Calculate a linearly interpolated percentile for numeric input.", ["number","percentile","statistics"], _number_percentile),
    ("json-escape-string", "JSON String Escaper", "Encode plain text as a valid JSON string literal.", ["json","escape","string"], _json_escape_string),
    ("json-unescape-string", "JSON String Decoder", "Decode a JSON string literal into plain text.", ["json","unescape","string"], _json_unescape_string),
    ("json-array-filter", "JSON Array Filter", "Filter an array of objects by an exact field value.", ["json","array","filter"], _json_array_filter),
    ("json-array-project", "JSON Array Projector", "Select named fields from each object in a JSON array.", ["json","array","project","select"], _json_array_project),
    ("json-diff", "JSON Diff", "Create a readable line diff between two JSON values.", ["json","diff","compare"], _json_diff),
    ("csv-to-markdown", "CSV to Markdown Table", "Render CSV rows as a Markdown table.", ["csv","markdown","table"], _csv_to_markdown),
    ("csv-merge", "CSV Merger", "Append rows from two CSV inputs when their headers match.", ["csv","merge","combine"], _csv_merge),
    ("csv-unique-count", "CSV Unique Counter", "Count distinct values in a selected CSV column.", ["csv","unique","count"], _csv_unique_count),
    ("csv-sample", "CSV Sampler", "Select a reproducible random sample of CSV rows.", ["csv","sample","random"], _csv_sample),
    ("number-standard-deviation", "Standard Deviation", "Calculate population or sample standard deviation.", ["number","standard deviation","statistics"], _number_standard_deviation),
    ("number-mode", "Number Mode", "Find the most frequent numeric value or values.", ["number","mode","statistics"], _number_mode),
    ("number-round", "Number Rounder", "Round a number to a configurable number of decimal places.", ["number","round","decimal"], _number_round),
    ("number-clamp", "Number Clamp", "Clamp a numeric value between inclusive minimum and maximum bounds.", ["number","clamp","limit"], _number_clamp),
    ("number-factorial", "Factorial Calculator", "Calculate factorial for an integer from 0 through 1000.", ["number","factorial","math"], _number_factorial),
    ("number-prime", "Prime Number Checker", "Check whether an integer is prime.", ["number","prime","math"], _number_prime),
    ("number-range", "Number Range Generator", "Generate a bounded integer sequence using start, stop, and step.", ["number","range","sequence"], _number_range),
    ("number-base-convert", "Number Base Converter", "Convert integers between bases 2 and 36.", ["number","base","convert"], _number_base_convert),
    ("percentage-calc", "Percentage Calculator", "Calculate a percentage of a base value.", ["percentage","percent","math"], _percentage_calc),
    ("unit-convert", "Unit Converter", "Convert common length or temperature units.", ["unit","convert","length","temperature"], _unit_convert),
    ("color-hex-rgb", "Hex to RGB Converter", "Convert a hexadecimal color into red, green, and blue channels.", ["color","hex","rgb"], _color_hex_rgb),
    ("color-rgb-hex", "RGB to Hex Converter", "Convert RGB channel values into a hexadecimal color.", ["color","rgb","hex"], _color_rgb_hex),
    ("ip-cidr-inspect", "CIDR Network Inspector", "Summarize a CIDR network range and host counts.", ["ip","cidr","network"], _ip_cidr_inspect),
    ("date-weekday", "Weekday Calculator", "Return the weekday name for an ISO date.", ["date","weekday","calendar"], _date_weekday),
    ("date-add-days", "Date Arithmetic", "Add or subtract a number of days from an ISO date.", ["date","add days","calendar"], _date_add_days),
    ("date-diff", "Date Difference", "Calculate the signed number of days between two ISO dates.", ("date", "difference", "calendar"), _date_diff),
    ("text-extract-emails", "Email Extractor", "Find email-like addresses in supplied text.", ["text","email","extract"], _make_extension_handler("text-extract-emails")),
    ("text-extract-urls", "URL Extractor", "Find HTTP and HTTPS URLs in supplied text.", ["text","url","extract"], _make_extension_handler("text-extract-urls")),
    ("text-extract-hashtags", "Hashtag Extractor", "Extract hashtag tokens from social text.", ["text","hashtag","social"], _make_extension_handler("text-extract-hashtags")),
    ("text-extract-mentions", "Mention Extractor", "Extract @mentions from social text.", ["text","mention","social"], _make_extension_handler("text-extract-mentions")),
    ("text-extract-phones", "Phone Pattern Extractor", "Extract phone-number-like strings for manual review.", ["text","phone","extract"], _make_extension_handler("text-extract-phones")),
    ("text-find-replace", "Literal Text Replacer", "Replace exact text without interpreting regular expressions.", ["text","replace","literal"], _make_extension_handler("text-find-replace")),
    ("text-nonempty-lines", "Non-empty Line Filter", "Keep only lines containing non-whitespace characters.", ["text","lines","filter"], _make_extension_handler("text-nonempty-lines")),
    ("text-common-prefix", "Common Prefix Finder", "Find the shared starting substring of two strings.", ["text","common prefix","compare"], _make_extension_handler("text-common-prefix")),
    ("text-common-suffix", "Common Suffix Finder", "Find the shared ending substring of two strings.", ["text","common suffix","compare"], _make_extension_handler("text-common-suffix")),
    ("text-word-count", "Word Counter", "Count whitespace-delimited words and unique tokens.", ["text","word count"], _make_extension_handler("text-word-count")),
    ("text-paragraph-count", "Paragraph Counter", "Count non-empty paragraphs separated by blank lines.", ["text","paragraph","count"], _make_extension_handler("text-paragraph-count")),
    ("text-title-case", "Title Case Formatter", "Convert text to title case.", ["text","title case","format"], _make_extension_handler("text-title-case")),
    ("text-similarity", "Text Similarity", "Compare two strings using a sequence similarity ratio.", ["text","similarity","compare"], _make_extension_handler("text-similarity")),
    ("text-quote-csv", "Text to CSV Field", "Quote a text value using CSV escaping rules.", ["text","csv","quote"], _make_extension_handler("text-quote-csv")),
    ("markdown-checklist", "Markdown Checklist Parser", "Extract checked and unchecked Markdown task items.", ["markdown","checklist","tasks"], _make_extension_handler("markdown-checklist")),
    ("markdown-frontmatter", "Markdown Front Matter Reader", "Read simple key-value front matter without a YAML dependency.", ["markdown","frontmatter","metadata"], _make_extension_handler("markdown-frontmatter")),
    ("markdown-heading-levels", "Markdown Heading Outline", "Extract Markdown headings with levels and source line numbers.", ["markdown","heading","outline"], _make_extension_handler("markdown-heading-levels")),
    ("json-deep-count", "JSON Structure Counter", "Count nested objects, arrays, keys, and scalar values recursively.", ["json","deep count","structure"], _make_extension_handler("json-deep-count")),
    ("json-array-sort", "JSON Array Sorter", "Sort a JSON array by a requested object field or scalar.", ["json","array","sort"], _make_extension_handler("json-array-sort")),
    ("json-array-dedupe", "JSON Array Deduplicator", "Remove duplicate JSON values while preserving first occurrence.", ["json","array","dedupe"], _make_extension_handler("json-array-dedupe")),
    ("csv-column-rename", "CSV Column Renamer", "Rename one CSV header while preserving rows.", ["csv","rename","column"], _make_extension_handler("csv-column-rename")),
    ("csv-filter-contains", "CSV Contains Filter", "Keep CSV rows where a selected column contains a text fragment.", ["csv","filter","contains"], _make_extension_handler("csv-filter-contains")),
    ("csv-filter-range", "CSV Numeric Range Filter", "Filter CSV rows by an inclusive numeric range.", ["csv","filter","range"], _make_extension_handler("csv-filter-range")),
    ("csv-pivot", "CSV Group Summary", "Group CSV rows and calculate counts or numeric sums.", ["csv","pivot","group"], _make_extension_handler("csv-pivot")),
    ("csv-validate", "CSV Schema Validator", "Check required headers and missing values in CSV rows.", ["csv","validate","schema"], _make_extension_handler("csv-validate")),
    ("python-ast-summary", "Python AST Summary", "Summarize top-level structure, functions, classes, and imports in Python source.", ["python","ast","summary"], _make_dev_extension_handler("python-ast-summary")),
    ("python-imports", "Python Import Extractor", "List unique imported modules from Python source.", ["python","imports","dependencies"], _make_dev_extension_handler("python-imports")),
    ("python-functions", "Python Function Finder", "List Python functions and async functions with line numbers.", ["python","functions","ast"], _make_dev_extension_handler("python-functions")),
    ("python-classes", "Python Class Finder", "List Python classes and their direct methods.", ["python","classes","ast"], _make_dev_extension_handler("python-classes")),
    ("lua-functions", "Lua Function Finder", "Extract named Lua function declarations and line numbers.", ["lua","functions","luau"], _make_dev_extension_handler("lua-functions")),
    ("lua-requires", "Lua Require Extractor", "Extract module names passed to Lua require calls.", ["lua","require","modules"], _make_dev_extension_handler("lua-requires")),
    ("js-imports", "JavaScript Import Extractor", "Extract import and require module specifiers.", ["javascript","imports","dependencies"], _make_dev_extension_handler("js-imports")),
    ("js-functions", "JavaScript Function Finder", "Find common named function and arrow-function declarations.", ["javascript","functions","source"], _make_dev_extension_handler("js-functions")),
    ("html-meta-extract", "HTML Metadata Extractor", "Extract title and name/property meta tag content.", ["html","meta","seo"], _make_dev_extension_handler("html-meta-extract")),
    ("xml-format", "XML Pretty Printer", "Validate and pretty-print XML text.", ["xml","format","pretty"], _make_dev_extension_handler("xml-format")),
    ("log-level-count", "Log Level Counter", "Count DEBUG, INFO, WARNING, ERROR, and CRITICAL labels.", ["log","levels","count"], _make_dev_extension_handler("log-level-count")),
    ("traceback-summary", "Traceback Summary", "Extract exception names and file-line frames from Python tracebacks.", ["traceback","exception","debug"], _make_dev_extension_handler("traceback-summary")),
    ("git-diff-stats", "Git Diff Statistics", "Count changed lines and file paths in a unified Git diff.", ["git","diff","statistics"], _make_dev_extension_handler("git-diff-stats")),
    ("semver-normalize", "Semantic Version Normalizer", "Normalize numeric MAJOR.MINOR.PATCH version strings.", ["semver","version","normalize"], _make_dev_extension_handler("semver-normalize")),
    ("semver-sort", "Semantic Version Sorter", "Sort numeric MAJOR.MINOR.PATCH version strings.", ["semver","version","sort"], _make_dev_extension_handler("semver-sort")),
    ("duration-parse", "Duration Parser", "Parse MM:SS or HH:MM:SS into total seconds.", ["duration","time","parse"], _make_dev_extension_handler("duration-parse")),
    ("image-dimensions", "Image Dimension Reader", "Read width and height from PNG or GIF headers; requires filesystem.read.", ["image","dimensions","metadata"], _make_dev_extension_handler("image-dimensions")),
    ("file-checksum", "File Checksum", "Calculate a cryptographic checksum of a file; requires filesystem.read.", ["file","checksum","sha256"], _make_dev_extension_handler("file-checksum")),
    ("directory-size", "Directory Size", "Measure file bytes in a directory tree; requires filesystem.read.", ["directory","size","filesystem"], _make_dev_extension_handler("directory-size")),
    ("file-size-human", "File Size Formatter", "Report file size in bytes and a human-readable unit; requires filesystem.read.", ["file","size","metadata"], _make_dev_extension_handler("file-size-human")),
    ("file-mime-guess", "MIME Type Guesser", "Guess MIME type from a filename extension.", ["mime","file","type"], _make_dev_extension_handler("file-mime-guess")),
    ("file-name-sanitize", "Filename Sanitizer", "Normalize a filename to a conservative character set.", ["filename","sanitize","file"], _make_dev_extension_handler("file-name-sanitize")),
    ("path-extension", "Path Extension Inspector", "Return basename, stem, and lowercase suffix for a path.", ["path","extension","filename"], _make_dev_extension_handler("path-extension")),
    ("code-fence-extract", "Markdown Code Fence Extractor", "Extract fenced code blocks and language labels.", ["markdown","code fence","extract"], _make_dev_extension_handler("code-fence-extract")),
    ("markdown-word-count", "Markdown Word Counter", "Count words in Markdown after removing heading markers.", ["markdown","word count","text"], _make_dev_extension_handler("markdown-word-count")),
    ("json-path-set", "JSON Path Setter", "Set a value at a dotted path in a JSON object copy.", ["json","path","set"], _make_data_extension_handler("json-path-set")),
    ("json-to-xml", "JSON to XML", "Convert JSON objects and arrays into simple XML elements.", ["json","xml","convert"], _make_data_extension_handler("json-to-xml")),
    ("xml-to-json", "XML to JSON", "Convert XML text structure into JSON.", ["xml","json","convert"], _make_data_extension_handler("xml-to-json")),
    ("html-heading-outline", "HTML Heading Outline", "Extract heading levels and visible heading text from HTML.", ["html","heading","outline"], _make_data_extension_handler("html-heading-outline")),
    ("html-image-extract", "HTML Image Extractor", "Extract image source and alternative text from HTML.", ["html","image","alt"], _make_data_extension_handler("html-image-extract")),
    ("http-header-parse", "HTTP Header Parser", "Parse raw HTTP header lines into a normalized mapping.", ["http","headers","parse"], _make_data_extension_handler("http-header-parse")),
    ("url-build", "URL Builder", "Build a URL from a base address and query parameters.", ["url","build","query"], _make_data_extension_handler("url-build")),
    ("email-validate", "Email Format Checker", "Check basic email syntax without verifying mailbox existence.", ["email","validate","format"], _make_data_extension_handler("email-validate")),
    ("phone-normalize", "Phone Normalizer", "Normalize phone-like text to digits and an optional leading plus.", ["phone","normalize","digits"], _make_data_extension_handler("phone-normalize")),
    ("password-strength", "Password Strength Heuristic", "Estimate password length and character-class variety without storing it.", ["password","strength","security"], _make_data_extension_handler("password-strength")),
    ("random-string", "Random String Generator", "Generate a random string using Python secrets.", ["random","string","generate"], _make_data_extension_handler("random-string")),
    ("lorem-generate", "Lorem Ipsum Generator", "Generate placeholder paragraphs for layout and typography testing.", ["lorem","placeholder","text"], _make_data_extension_handler("lorem-generate")),
    ("uuid-parse", "UUID Inspector", "Validate a UUID and return its canonical form and variant.", ["uuid","parse","inspect"], _make_data_extension_handler("uuid-parse")),
    ("timestamp-convert", "Timestamp Converter", "Convert between Unix timestamps and ISO date-times.", ["timestamp","unix","datetime"], _make_data_extension_handler("timestamp-convert")),
    ("timezone-convert", "Timezone Converter", "Convert ISO date-times into a requested IANA timezone.", ["timezone","convert","datetime"], _make_data_extension_handler("timezone-convert")),
    ("file-find", "File Finder", "Find files or directories by glob pattern; requires filesystem.read.", ["file","find","glob"], _make_data_extension_handler("file-find")),
    ("file-text-search", "File Text Search", "Search UTF-8 text files for a phrase; requires filesystem.read.", ["file","search","text"], _make_data_extension_handler("file-text-search")),
    ("duplicate-files", "Duplicate File Finder", "Group duplicate files by size and SHA-256; requires filesystem.read.", ["file","duplicate","checksum"], _make_data_extension_handler("duplicate-files")),
    ("directory-tree", "Directory Tree", "Create a bounded directory tree listing; requires filesystem.read.", ["directory","tree","folder"], _make_data_extension_handler("directory-tree")),
    ("file-extension-count", "File Extension Counter", "Count file extensions in a directory tree; requires filesystem.read.", ["file","extension","count"], _make_data_extension_handler("file-extension-count")),
    ("xml-attrs-extract", "XML Attribute Extractor", "Extract XML element attributes into structured records.", ["xml","attributes","extract"], _make_data_extension_handler("xml-attrs-extract")),
    ("css-colors-extract", "CSS Color Extractor", "Extract unique hexadecimal color literals from CSS.", ["css","color","extract"], _make_data_extension_handler("css-colors-extract")),
    ("css-rule-count", "CSS Rule Counter", "Count CSS selectors and declarations while ignoring block comments.", ["css","rules","count"], _make_data_extension_handler("css-rule-count")),
    ("html-form-inspect", "HTML Form Inspector", "Inspect form actions, methods, and named input fields.", ["html","form","inspect"], _make_data_extension_handler("html-form-inspect")),
    ("html-table-extract", "HTML Table Extractor", "Extract rows and cell text from HTML tables.", ["html","table","extract"], _make_data_extension_handler("html-table-extract")),
    ("file-line-count", "File Line Counter", "Count UTF-8 text lines and characters; requires filesystem.read.", ["file","line count","text"], _make_final_extension_handler("file-line-count")),
    ("file-head", "File Head", "Read the first N UTF-8 text lines; requires filesystem.read.", ["file","head","preview"], _make_final_extension_handler("file-head")),
    ("file-tail", "File Tail", "Read the last N UTF-8 text lines; requires filesystem.read.", ["file","tail","preview"], _make_final_extension_handler("file-tail")),
    ("file-json-inspect", "JSON File Inspector", "Parse a JSON file and summarize its top-level shape; requires filesystem.read.", ["file","json","inspect"], _make_final_extension_handler("file-json-inspect")),
    ("archive-create", "ZIP Archive Creator", "Create a ZIP from named text entries; requires filesystem.write.", ["zip","archive","create"], _make_final_extension_handler("archive-create")),
    ("archive-extract-safe", "Safe ZIP Extractor", "Extract bounded ZIP contents with path traversal checks; requires filesystem.read and filesystem.write.", ["zip","archive","extract"], _make_final_extension_handler("archive-extract-safe")),
    ("file-copy", "File Copier", "Copy a file without overwriting an existing destination; requires read and write permissions.", ["file","copy"], _make_final_extension_handler("file-copy")),
    ("file-rename", "File Renamer", "Rename a file within its current directory without overwriting; requires filesystem.write.", ["file","rename"], _make_final_extension_handler("file-rename")),
    ("directory-empty-check", "Directory Empty Checker", "Check whether a directory contains any entries; requires filesystem.read.", ["directory","empty","folder"], _make_final_extension_handler("directory-empty-check")),
    ("json-schema-lite", "JSON Schema Lite Validator", "Check basic JSON type, required keys, and property types.", ["json","schema","validate"], _make_final_extension_handler("json-schema-lite")),
    ("json-redact-keys", "JSON Secret Redactor", "Recursively redact selected keys in JSON data.", ["json","redact","privacy"], _make_final_extension_handler("json-redact-keys")),
    ("xml-element-paths", "XML Element Path Finder", "List element paths, tags, and attributes in an XML document.", ["xml","paths","structure"], _make_final_extension_handler("xml-element-paths")),
    ("text-compare-lines", "Line-by-Line Text Comparator", "Compare two texts by line position and report differences.", ["text","compare","lines"], _make_final_extension_handler("text-compare-lines")),
    ("todo-extract", "TODO Marker Extractor", "Find TODO, FIXME, and BUG markers with line numbers.", ["todo","fixme","code"], _make_final_extension_handler("todo-extract")),
    ("number-gcd-lcm", "GCD and LCM Calculator", "Calculate greatest common divisor and least common multiple.", ["number","gcd","lcm"], _make_final_extension_handler("number-gcd-lcm")),
    ("number-roman", "Roman Numeral Converter", "Convert integers from 1 to 3999 into Roman numerals.", ["number","roman","convert"], _make_final_extension_handler("number-roman")),
    ("color-rgb-hsl", "RGB to HSL Converter", "Convert RGB color channels to HSL values.", ["color","rgb","hsl"], _make_final_extension_handler("color-rgb-hsl")),
    ("color-hsl-rgb", "HSL to RGB Converter", "Convert HSL color values to RGB channels.", ["color","hsl","rgb"], _make_final_extension_handler("color-hsl-rgb")),
    ("date-month-calendar", "Month Calendar Generator", "Generate a Monday-first calendar grid for a year and month.", ["date","calendar","month"], _make_final_extension_handler("date-month-calendar")),
    ("date-week-number", "ISO Week Calculator", "Return ISO year, week number, and weekday for a date.", ["date","week","calendar"], _make_final_extension_handler("date-week-number")),
    ("url-safe-check", "HTTP URL Format Checker", "Check URL structure and reject credentials or unsupported schemes.", ["url","validate","http"], _make_final_extension_handler("url-safe-check")),
    ("html-link-domain-count", "HTML Link Domain Counter", "Count HTML anchor links grouped by destination hostname.", ["html","link","domain"], _make_final_extension_handler("html-link-domain-count")),
    ("css-variable-extract", "CSS Variable Extractor", "Extract CSS custom property declarations.", ["css","variables","theme"], _make_final_extension_handler("css-variable-extract")),
    ("jsonl-to-json", "JSONL to JSON", "Convert newline-delimited JSON records into a formatted JSON array.", ["jsonl","json","convert"], _make_final_extension_handler("jsonl-to-json")),
    ("json-to-jsonl", "JSON to JSONL", "Convert a JSON array into newline-delimited JSON records.", ["json","jsonl","convert"], _make_final_extension_handler("json-to-jsonl")),
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
    ("ui-builder", "Design and implement UI layouts, reusable components, and interaction states.", "build UI, interface, dashboard, components", "Confirm target platform and framework. Map the main user flow. Define layout hierarchy, reusable components, responsive breakpoints, and loading, empty, error, and success states. Implement real controls with accessible labels and keyboard or touch behavior. Run available build and interaction tests; do not describe a static mockup as a working application."),
    ("web-research", "Retrieve and verify information from live websites and primary sources.", "browse web, open website, online research", "Use an available browser or web-search connector. Never claim to open a page without retrieval. Prioritize primary sources, verify dates, compare claims, cite sources, and distinguish public pages from authenticated or blocked content."),
    ("video-analysis", "Analyze supplied video files or accessible video sources.", "analyze video, watch video, video summary", "Confirm video data or an authorized video-analysis tool is available. Inspect frames with timestamps and transcribe speech only when supported. Report visible scenes and events; separate observation from inference. Never claim to watch an inaccessible link."),
    ("image-creation", "Create original visual assets from a clear design brief.", "generate image, create artwork, illustration", "Translate the brief into subject, composition, style, palette, aspect ratio, and constraints. Use an available image-generation tool. For edits, change only requested details. State clearly when output is raster rather than editable vector."),
    ("audio-transcription", "Transcribe accessible audio with speaker turns where possible.", "transcribe audio, speech to text", "Use an available audio transcription capability. Preserve speaker turns when distinguishable and timestamps when supported. Mark uncertain words; do not invent speech or claim to process missing audio."),
    ("frontend-development", "Build responsive frontend pages and reusable components.", "frontend, HTML CSS JS, React", "Inspect the existing stack. Implement semantic responsive UI, accessible labels, keyboard states, and real interactions. Avoid fake backend behavior. Run lint, build, and tests when available and report exact outcomes."),
    ("backend-development", "Implement server endpoints, validation, and business logic.", "backend, API server, endpoint", "Confirm framework, authentication, and data model. Define request and response contracts, validation, safe errors, and tests. Keep secrets out of source and logs. Do not describe a mock endpoint as deployed."),
    ("browser-automation", "Perform authorized multi-step browser workflows.", "browser automation, click website, fill form", "Use a connected browser tool only when available and authorized. Inspect page state before actions. Confirm irreversible steps. Do not bypass CAPTCHAs or access controls; report blocked steps honestly."),
    ("accessibility-audit", "Review interfaces against practical accessibility requirements.", "accessibility, WCAG, screen reader", "Check semantics, keyboard navigation, focus visibility, labels, alt text, heading order, error messages, and contrast. Treat automated scans as hints, not proof of compliance. Provide severity and concrete fixes."),
    ("data-visualization", "Choose and create clear charts from structured data.", "chart, graph, visualize data", "Inspect columns, units, missing values, and comparison goal. Choose a suitable chart, label axes, avoid misleading scales, and state limitations. Generate charts only from supplied or retrieved data."),
    ("web-page-reading", "Read static web pages carefully and extract grounded information.", "read web page, inspect page, website content", "Use the public page reader only for pages reachable without login. Capture title, URL, response status, and relevant text. Do not claim to execute JavaScript or interact with controls. Cite the page URL and distinguish page content from interpretation."),
    ("video-storyboard", "Turn video content into a timestamped scene-by-scene storyboard.", "storyboard, video scenes, shot list", "Use supplied video frames or an accessible video inspection tool. Group shots by scene, note timestamps, camera movement, visible subjects, and transitions. Keep observations literal and flag missing frames or uncertain timing."),
    ("video-captioning", "Create readable captions from accessible video speech.", "video captions, subtitles, SRT, captions", "Obtain audio through a supported upload or transcription tool. Preserve meaning and speaker changes, use concise caption lengths, and add timestamps only when supported. Do not fabricate dialogue or infer words from silent footage."),
    ("audio-analysis", "Describe accessible audio content and sound structure.", "analyze audio, audio summary, recording review", "Confirm that audio data or a transcription is present. Summarize speech, speaker turns, pauses, and non-speech sounds only when audible. Separate acoustic observations from assumptions and note recording limitations."),
    ("audio-cleanup", "Prepare a safe cleanup plan for noisy audio recordings.", "audio cleanup, noise reduction, normalize audio", "Inspect the source and requested output. Recommend noise reduction, gating, equalization, and loudness normalization conservatively. Keep an untouched original and render only through an available audio-processing tool."),
    ("ux-writing", "Write concise interface labels, helper text, and error messages.", "UX writing, microcopy, button labels", "Identify user intent and context for each screen. Use clear action labels, helpful validation, and non-blaming errors. Preserve terminology and keep text concise; include success, empty, loading, and failure states."),
    ("component-library", "Design reusable UI components with consistent behavior.", "component library, design components, UI kit", "Identify shared patterns and framework conventions. Define component APIs, variants, states, accessibility, and responsive behavior. Avoid duplicating near-identical components and document usage examples."),
    ("mobile-ui-design", "Design touch-friendly interfaces for small screens.", "mobile UI, phone layout, responsive app", "Prioritize the primary task and thumb reach. Define safe areas, readable type, touch target sizes, scroll behavior, keyboard handling, and offline/error states. Test narrow and larger phone widths."),
    ("design-system", "Create a coherent visual design system for a product.", "design system, theme, tokens, typography", "Define color, typography, spacing, radius, elevation, icon, and motion tokens. Specify semantic roles and contrast requirements. Map tokens to components and document theme usage."),
    ("prompt-engineering", "Develop structured prompts with measurable output requirements.", "prompt engineering, improve prompt, system prompt", "Define objective, context, constraints, input format, output schema, and failure behavior. Include examples. Test representative edge cases and refine based on observed results, not claims."),
    ("test-automation", "Create repeatable automated checks for product behavior.", "automation test, browser test, regression test", "Choose an appropriate test layer. Use deterministic fixtures, stable selectors, and explicit assertions. Cover normal, edge, and failure paths. Keep tests isolated and report exact command and environment."),
    ("ci-cd", "Design build, test, and deployment pipelines.", "CI CD, GitHub Actions, build pipeline", "Inspect repository tooling and deployment targets. Define triggers, caching, quality gates, secrets handling, artifacts, and rollback. Run workflows on non-production branches before enabling releases."),
    ("deployment-readiness", "Assess whether an application is safe to release.", "deployment checklist, production readiness", "Review configuration, secrets, health checks, migrations, monitoring, backup, rollback, and security. Identify blocking gaps and assign verification steps. Never call a release ready when critical checks remain unknown."),
    ("observability", "Design logs, metrics, traces, and actionable alerts.", "observability, monitoring, logs, metrics", "Define service-level indicators and failure modes. Use structured logs without secrets, metrics with bounded cardinality, and traces across dependencies. Set alerts tied to user impact and document response playbooks."),
    ("documentation-review", "Audit documentation for correctness, completeness, and usability.", "review docs, audit README, docs quality", "Compare each claim against current implementation. Check prerequisites, examples, links, error cases, permissions, version assumptions, and limitations. Flag stale claims and offer corrected wording."),
    ("ui-prototyping", "Create functional low- and high-fidelity UI prototypes.", "prototype UI, interactive mockup, wireframe", "Translate user goals into screens and navigation. Define component states and realistic sample data. Use clickable prototypes for flow validation and label non-functional controls. Review on mobile and desktop before implementation."),
    ("dashboard-design", "Design dashboards that make key metrics and actions easy to scan.", "dashboard, admin panel, analytics UI", "Identify the user roles, decisions, and key performance indicators. Prioritize trends and exceptions over decorative charts. Define filters, date ranges, drill-downs, empty states, and responsive behavior."),
    ("mobile-usability", "Evaluate and improve usability on phones and tablets.", "mobile usability, touch interface, phone UX", "Test primary tasks at common viewport sizes. Check touch targets, thumb reach, keyboard overlap, scrolling, orientation, load states, and readable text. Record concrete friction and fixes."),
    ("web-accessibility-testing", "Test web interfaces using keyboard and assistive-technology principles.", "web accessibility test, WCAG check", "Navigate without a mouse, inspect focus order, labels, landmarks, headings, status announcements, and contrast. Use automated scanners as a supplement. Document reproducible failures and avoid claiming certification."),
    ("web-fact-checking", "Verify factual claims found on websites.", "fact check website, verify claim online", "Break a claim into checkable parts. Search primary records and independent corroboration. Check publication and event dates, methodology, and context. State whether evidence supports, contradicts, or cannot resolve each part."),
    ("video-edit-planning", "Create a practical video editing timeline and export plan.", "video edit plan, editing timeline, montage", "Review supplied footage or shot notes. Plan sequence, timestamps, cuts, pacing, transitions, captions, music cues, and aspect ratio. Specify export settings. Render only when a video editor is available."),
    ("subtitle-review", "Review subtitles for timing, readability, and translation accuracy.", "subtitle review, SRT review, captions proofreading", "Check timing overlap, reading speed, line length, speaker attribution, punctuation, and terminology. Compare translated lines with source meaning. Mark uncertain audio rather than inventing corrections."),
    ("animation-direction", "Specify motion principles and animation behavior for interfaces or video.", "animation design, motion graphics, transitions", "Define purpose, duration, easing, sequence, and reduced-motion behavior. Keep motion consistent with hierarchy and feedback. Avoid decorative movement that obscures content or harms accessibility."),
    ("icon-design", "Create a coherent icon family for products and dashboards.", "icon set, UI icons, icon design", "Define a grid, stroke weight, corner language, optical alignment, and filled/outline variants. Check meaning at small sizes and contrast on all themes. Avoid copying proprietary icon artwork."),
    ("design-critique", "Review visual designs and provide prioritized actionable feedback.", "design critique, review UI, visual feedback", "Evaluate hierarchy, alignment, spacing, typography, color, consistency, accessibility, and task fit. Separate objective defects from taste. Give prioritized fixes with examples and preserve the intended brand direction."),
    ("ux-research", "Plan and synthesize user research to discover needs and friction.", "UX research, user interviews, research synthesis", "Set research questions and participant criteria. Use neutral interview prompts and informed consent. Synthesize observations into themes, evidence, and opportunity areas. Do not present a small sample as representative of all users."),
    ("usability-testing", "Plan and analyze task-based usability tests.", "usability test, user testing, test session", "Write realistic tasks and success criteria. Avoid leading participants. Record completion, errors, time, and observations where consented. Separate usability findings from proposed solutions and prioritize by impact."),
    ("information-architecture", "Organize content and navigation around user mental models.", "information architecture, navigation, sitemap", "Inventory content and user tasks. Group related topics, define labels, and test navigation with representative users. Produce a sitemap and menu hierarchy, noting governance and naming decisions."),
    ("content-design", "Design helpful content for product journeys and complex tasks.", "content design, product content, user guidance", "Map user intent and information needs at each step. Write concise headings, instructions, validation, and next steps. Test comprehension, preserve terminology, and plan localization and accessibility."),
    ("product-design", "Connect user needs, product constraints, and interface decisions.", "product design, feature design", "Clarify user problem, business outcome, and constraints. Map journeys, define success metrics, explore alternatives, and align UX, technical feasibility, and delivery. Document assumptions and trade-offs."),
    ("data-engineering", "Design reliable data ingestion, transformation, and storage workflows.", "data engineering, ETL, ingestion pipeline", "Map sources, schema, volume, latency, and data sensitivity. Define idempotent ingestion, validation, retries, lineage, partitioning, and retention. Include monitoring and replay strategy."),
    ("data-pipeline-design", "Build observable and fault-tolerant data pipeline plans.", "data pipeline, batch jobs, streaming", "Specify triggers, stages, schemas, checkpoints, late-arriving data, retries, and dead-letter handling. Define freshness and completeness metrics. Prefer reproducible transformations and safe backfills."),
    ("database-optimization", "Improve database performance using measured workload evidence.", "database performance, index tuning", "Inspect query patterns, table sizes, indexes, and query plans. Measure baseline latency and throughput. Recommend indexes or schema changes with write-cost trade-offs. Verify on representative data."),
    ("query-optimization", "Rewrite slow SQL queries without changing their meaning.", "SQL performance, optimize query", "Confirm dialect and expected results. Examine joins, filters, cardinality, indexes, and execution plan. Compare result equivalence and benchmark on representative data. Parameterize user-supplied values."),
    ("data-quality-audit", "Audit datasets for completeness, validity, uniqueness, and consistency.", "data quality, data audit, anomalies", "Define domain rules and expected schema. Profile missing values, duplicates, outliers, referential integrity, and freshness. Quantify issues, preserve raw data, and propose validation gates."),
    ("ml-experiment-design", "Plan reproducible machine-learning experiments.", "ML experiment, model training plan", "Define task, baseline, data splits, leakage risks, metrics, and hypothesis. Control random seeds and document configuration. Separate tuning data from final evaluation and report compute constraints."),
    ("model-evaluation", "Evaluate model outputs against quality, safety, and reliability criteria.", "model evaluation, LLM eval, benchmark", "Define representative cases and rubrics before testing. Measure correctness, calibration, latency, cost, robustness, and safety where relevant. Report sample limitations and compare to a baseline."),
    ("prompt-testing", "Systematically test prompts across normal and adversarial inputs.", "prompt evaluation, test prompts", "Create a balanced test set with edge cases and ambiguous requests. Define measurable rubric and expected outputs. Compare revisions using identical cases and track regressions. Do not optimize only for cherry-picked examples."),
    ("support-triage", "Classify support requests and route urgent issues safely.", "support triage, ticket priority", "Identify impact, affected users, urgency, and reproducibility. Ask only essential questions. Route security, privacy, billing, or outage issues to the right owner. Never request passwords or secret tokens."),
    ("release-notes", "Write accurate, user-facing release notes from merged changes.", "release notes, changelog writing", "Review merged commits and verified behavior. Group changes into added, improved, fixed, and known issues. Explain user impact in plain language and omit speculative or unshipped work."),
    ("vector-graphics", "Plan or create clean vector-style graphics and icons.", "vector graphic, SVG illustration, vector design", "Define canvas, geometry, stroke, fills, and reusable shapes. Prefer editable SVG paths and semantic grouping when source is required. Check scaling, contrast, and small-size legibility. Do not call a raster image a vector file."),
    ("infographic-design", "Turn verified information into a clear visual infographic.", "infographic, visual explainer", "Choose one core message and a simple reading path. Verify numbers and sources before visualizing. Use labels, proportional visual encoding, and accessible contrast. Avoid decorative charts that distort comparisons."),
    ("iconography-review", "Audit icon consistency and meaning across an interface.", "icon review, icon system, UI icon consistency", "Compare grid, stroke, corner radius, optical size, filled/outline language, and meaning. Identify ambiguous or redundant symbols and recommend corrections. Verify labels for icons that are not universally understood."),
    ("brand-guidelines", "Write practical brand usage rules for a product or organization.", "brand guideline, brand book, identity rules", "Define logo clear space, minimum size, color values, typography, imagery, voice, and prohibited treatments. Include examples for light/dark backgrounds and small avatars. Keep rules specific enough to enforce."),
    ("typography-review", "Improve typographic hierarchy, readability, and consistency.", "typography audit, font pairing, type scale", "Inspect type roles, sizes, weights, line lengths, line heights, and responsive scaling. Check language coverage and small-screen readability. Recommend a consistent scale and avoid unnecessary font variety."),
    ("motion-design", "Plan motion graphics and transitions for a narrative or product.", "motion design, motion graphics, animated sequence", "Define message, pacing, keyframes, transitions, easing, and sound alignment. Keep text readable and use consistent movement grammar. Respect reduced-motion preferences for interface animation."),
    ("interaction-design", "Specify how controls and user flows behave across states.", "interaction design, UX interactions", "Define triggers, feedback, state transitions, validation, undo, and recovery. Cover keyboard, touch, pointer, and assistive technology. Ensure controls communicate their state and never behave as decorative-only elements."),
    ("service-design", "Map the end-to-end service experience across people and systems.", "service design, service blueprint", "Map customer actions, frontstage touchpoints, backstage processes, systems, and handoffs. Identify failure points, wait states, and ownership. Define evidence and service-level outcomes for improvements."),
    ("customer-journey-mapping", "Map customer goals, emotions, touchpoints, and pain points.", "customer journey, journey map", "Specify persona or segment and journey scope. Break the journey into stages, actions, questions, and friction. Distinguish research evidence from assumptions and identify measurable opportunities."),
    ("competitive-analysis", "Compare products using consistent criteria and evidence.", "competitor analysis, product comparison", "Define the category, audience, and comparison dimensions. Use current primary product information and cite it. Compare features, pricing, positioning, and trade-offs without inventing competitor capabilities."),
    ("market-research", "Structure market research and assess evidence quality.", "market research, market size, industry analysis", "Define segment, geography, timeframe, and decision. Prefer authoritative datasets and transparent methodologies. Distinguish TAM/SAM/SOM assumptions from measured figures and explain confidence and gaps."),
    ("technical-diagramming", "Create accurate technical diagrams from system behavior.", "architecture diagram, sequence diagram, flowchart", "Identify actors, boundaries, data flows, and failure paths. Choose a diagram type that answers one question. Label protocols and directions accurately and verify every connection against implementation."),
    ("architecture-review", "Review a proposed system architecture for fit and risk.", "software architecture review, system design", "Assess requirements, boundaries, dependencies, scalability, resilience, security, and operability. Surface trade-offs and failure modes. Tie recommendations to workload assumptions and avoid speculative complexity."),
    ("microservice-design", "Design service boundaries and contracts for distributed systems.", "microservice architecture, service boundary", "Start from domain capabilities and data ownership. Define service APIs, consistency, events, retries, idempotency, and observability. Challenge unnecessary service splitting and account for distributed failure."),
    ("api-design", "Design clear, stable, versionable API contracts.", "REST API design, endpoint contract", "Define resources, methods, schemas, errors, pagination, auth, and idempotency. Use consistent naming and versioning policy. Include example requests/responses and compatibility expectations."),
    ("security-testing", "Plan authorized security tests for an application.", "security test, penetration test plan", "Confirm scope and authorization. Prioritize input validation, auth, access control, secrets, dependency risk, and abuse cases. Use safe test environments and report reproducible findings without destructive exploitation."),
    ("threat-modeling", "Map threats and mitigations across application trust boundaries.", "threat model, STRIDE, attack surface", "Identify assets, actors, entry points, trust boundaries, and abuse cases. Rate impact and likelihood. Propose mitigations and residual risk. Revisit the model when architecture or data flows change."),
    ("incident-postmortem", "Write a blameless incident review with actionable prevention.", "postmortem, incident review, outage report", "Build a verified timeline and impact summary. Explain contributing factors rather than assigning blame. Record what worked, what failed, and measurable corrective actions with owners and dates."),
    ("privacy-impact-assessment", "Assess privacy consequences of proposed data processing.", "privacy impact, DPIA, data processing", "Map data categories, purpose, legal/consent assumptions, recipients, storage, retention, and user rights. Minimize data and identify risks and mitigations. Refer legal conclusions to qualified counsel."),
    ("governance-review", "Review ownership, policy, risk, and accountability for a project.", "governance, policy review, accountability", "Identify decision rights, roles, policy obligations, records, and escalation paths. Test whether controls are measurable and auditable. Separate established obligations from recommendations or unresolved interpretations."),
    ("data-storytelling", "Communicate data findings with a clear narrative and caveats.", "data storytelling, insight narrative", "Start with the decision or question. Select a small number of defensible findings and visuals. Explain context, uncertainty, and limitations. Keep observation, interpretation, and recommendation distinct."),
    ("statistical-analysis", "Choose and explain statistical methods for a dataset or question.", "statistics, statistical test, hypothesis test", "Inspect sampling, distributions, missing data, and assumptions. Select methods appropriate to the design. Report effect sizes and uncertainty, not just p-values. Avoid causal claims from observational association."),
    ("experimentation", "Design controlled experiments and interpret their results.", "experiment design, A/B test", "Define hypothesis, target metric, guardrails, randomization, sample size assumptions, and stopping policy. Check instrumentation and segment balance. Report uncertainty and practical significance."),
    ("prompt-library-management", "Organize reusable prompts with versioning and evaluation notes.", "prompt library, prompt catalog", "Group prompts by task and owner. Document variables, model assumptions, examples, and known limits. Version revisions and attach a representative evaluation set. Remove stale or duplicate prompt entries."),
    ("knowledge-base-design", "Design a searchable knowledge base with clear governance.", "knowledge base, FAQ architecture", "Identify audience, recurring questions, source of truth, owners, and review cadence. Use consistent taxonomy, metadata, and article templates. Include freshness indicators and escalation paths when answers are unavailable."),
    ("technical-translation", "Translate technical content while preserving terminology and code context.", "technical translation, translate documentation", "Identify the target audience and locale. Preserve code, placeholders, commands, units, identifiers, and product names. Maintain an approved glossary and flag ambiguous terms. Review the translation against the source for completeness."),
    ("copyediting", "Improve grammar, flow, consistency, and readability in finished drafts.", "copyedit, copy editing, proofread", "Preserve the author's meaning and facts. Correct grammar, punctuation, flow, and consistency. Apply the requested style guide and return a clean version plus a short change summary when useful."),
    ("product-copywriting", "Write persuasive product copy grounded in actual features.", "product copy, product description, landing page", "Identify audience, problem, differentiator, proof, and call to action. Use specific benefits supported by verified features. Avoid fabricated claims, guarantees, or unsupported comparisons."),
    ("longform-writing", "Structure and draft long-form articles or guides.", "longform, article, essay, guide writing", "Define audience, purpose, thesis, and scope. Build a logical outline, support claims with credible evidence, and keep sections coherent. Avoid repetition and cite factual assertions."),
    ("academic-writing", "Improve academic structure, argumentation, and citation discipline.", "academic writing, paper, essay", "Clarify research question, claim, method, evidence, and limitations. Keep citations attached to supported claims. Distinguish analysis from sources and avoid inventing references or results."),
    ("grant-writing", "Prepare evidence-led grant applications and project narratives.", "grant proposal, funding application", "Extract eligibility, evaluation criteria, budget rules, and deadlines from the funder's official guidance. Align objectives, activities, outcomes, and evaluation. Never invent organizational credentials or commitments."),
    ("policy-writing", "Draft clear internal policies with scope and enforcement rules.", "policy document, company policy", "Define purpose, scope, roles, rules, exceptions, reporting, and review cadence. Use enforceable language and align with verified requirements. Flag legal or regulatory issues for qualified review."),
    ("incident-communications", "Prepare accurate updates during technical incidents.", "incident update, outage communication", "Confirm current impact, affected services, mitigation, and next update time. Use plain language, avoid blame and speculation, and keep internal details secure. Update only when facts change."),
    ("executive-briefing", "Turn complex work into a decision-ready executive brief.", "executive summary, leadership briefing", "Lead with the decision needed, recommendation, impact, cost, and risk. Keep evidence concise and traceable. State assumptions, options, and unresolved questions without hiding uncertainty."),
    ("board-reporting", "Prepare concise board-level reports and governance updates.", "board report, board presentation", "Focus on strategic progress, financial or operational indicators, major risks, decisions, and accountability. Verify every figure and define metrics. Avoid activity lists without outcomes."),
    ("stakeholder-management", "Map stakeholders and plan communication and decision paths.", "stakeholder plan, stakeholder analysis", "Identify affected groups, influence, interests, and information needs. Define owners, cadence, channels, and escalation. Track decisions and feedback while avoiding unnecessary personal data."),
    ("project-risk-management", "Maintain a practical project risk register and mitigation plan.", "project risk register, manage project risks", "Record risk statement, cause, likelihood, impact, trigger, owner, response, and residual risk. Review regularly and tie mitigations to milestones. Separate current risks from closed issues."),
    ("portfolio-management", "Prioritize and balance a portfolio of competing initiatives.", "project portfolio, portfolio prioritization", "Define strategic alignment, value, effort, dependencies, capacity, and risk criteria. Compare initiatives transparently and show trade-offs. Do not imply subjective scoring is objective."),
    ("agile-facilitation", "Facilitate agile ceremonies with clear outcomes and follow-through.", "agile facilitator, scrum ceremony", "Set a clear purpose and timebox. Invite concise participation, surface blockers, and capture decisions and owners. Keep ceremonies focused on delivery outcomes rather than status theater."),
    ("sprint-planning", "Turn prioritized backlog items into a realistic sprint goal and plan.", "sprint planning, sprint goal", "Review team capacity, priorities, dependencies, and acceptance criteria. Agree one outcome-based sprint goal and select work based on demonstrated throughput, not wishful commitments."),
    ("backlog-refinement", "Improve backlog item clarity, sequencing, and readiness.", "backlog refinement, user story", "Clarify user value, scope, dependencies, acceptance criteria, and open questions. Split oversized work and surface uncertainty. Avoid estimating before the team understands the item."),
    ("requirements-analysis", "Elicit, structure, and validate business and system requirements.", "requirements analysis, requirement document", "Identify stakeholders, goals, constraints, and exceptions. Distinguish functional, non-functional, and regulatory needs. Make requirements testable and traceable to business outcomes."),
    ("business-analysis", "Analyze business processes and convert findings into actionable requirements.", "business analysis, process analysis", "Map current state, pain points, actors, data, and outcomes. Validate root causes with evidence. Define future-state options, measurable benefits, assumptions, and dependencies."),
    ("process-improvement", "Identify waste and redesign processes for measurable outcomes.", "process improvement, workflow optimization", "Map the actual process, handoffs, wait time, rework, and failure points. Establish a baseline and choose a small improvement. Measure impact and prevent regression."),
    ("operations-playbook", "Write operational runbooks for repeatable tasks and incidents.", "runbook, operations playbook", "State purpose, prerequisites, access, steps, verification, rollback, escalation, and ownership. Use copyable safe commands and warn before destructive actions. Test instructions with a fresh operator."),
    ("financial-model-review", "Review financial models for logic, assumptions, and scenario integrity.", "financial model, forecast review", "Check units, formulas, input assumptions, dependencies, and scenario controls. Reconcile totals and sensitivity cases. Label estimates and do not present projections as guaranteed outcomes."),
    ("budgeting-analysis", "Analyze budgets, variances, and spending trade-offs.", "budget analysis, budget variance", "Check period, currency, accounting basis, and category definitions. Compare actuals to budget, explain variance drivers, and identify one-time effects. Verify totals and state data gaps."),
    ("pricing-strategy", "Evaluate pricing options against value, costs, and market context.", "pricing strategy, price model", "Identify segments, value metrics, costs, alternatives, and willingness-to-pay evidence. Model tiering and trade-offs. Avoid unsupported competitor price claims and validate with customer research."),
    ("vendor-evaluation", "Compare vendors using consistent criteria and documented evidence.", "vendor selection, vendor review", "Define mandatory requirements, security, privacy, cost, reliability, support, and exit criteria. Score evidence consistently and record gaps. Do not infer compliance from marketing statements."),
    ("contract-review", "Summarize contract clauses and flag issues for qualified legal review.", "contract review, agreement analysis", "Identify parties, scope, fees, term, renewal, termination, liability, data handling, confidentiality, IP, and dispute clauses. Quote exact clause references. Do not provide legal conclusions or substitute for counsel."),
    ("python-testing", "Design tests for Python packages and applications.", "python tests, pytest, unittest", "Inspect existing test conventions. Add deterministic tests for public behavior, boundaries, invalid input, permissions, and regressions. Use temporary files and mocks for external services. Run the exact test command and report failures."),
    ("lua-script-review", "Review Lua or Luau scripts for correctness and runtime assumptions.", "review Lua, Luau script review, Roblox code review", "Confirm runtime and API availability. Trace event lifecycles, state ownership, cleanup, and client/server boundaries. Identify concrete bugs and unsafe assumptions with file and line references. Preserve intended behavior."),
    ("game-ui-development", "Build game interfaces that remain responsive and performant in-game.", "game UI, Roblox UI, game panel", "Identify platform APIs, input modes, safe areas, and performance limits. Define panel hierarchy, touch targets, toggles, sliders, dropdowns, and feedback. Avoid heavy animation on low-end devices and test actual states."),
    ("roblox-luau-development", "Develop maintainable Roblox Luau modules and interfaces.", "Roblox Luau, Roblox script, RemoteEvent", "Use documented Roblox services and Luau conventions. Separate client visuals from server authority, validate RemoteEvent inputs, and clean up connections. State assumptions about Studio or other runtime explicitly."),
    ("web-frontend-accessibility", "Build accessible browser UI with responsive interaction states.", "frontend accessibility, accessible website", "Use semantic HTML, labels, keyboard focus, contrast, headings, and accessible errors. Test responsive behavior and reduced-motion preferences. Avoid replacing native controls without a clear need."),
    ("web-content-operations", "Plan and maintain accurate website content across pages.", "website content, web content ops", "Define page purpose, audience, owner, source, update cadence, and metadata. Keep facts current and links valid. Establish a review workflow and change history for important content."),
    ("browser-research", "Conduct structured research using a live browser and source notes.", "browser research, investigate website", "Use an authorized browser or web search capability. Record search terms, source dates, relevant passages, and URLs. Cross-check key claims and note pages that are blocked or require sign-in."),
    ("video-asset-management", "Organize video files, metadata, and project assets.", "video assets, footage organization", "Define naming, folder structure, proxies, source backups, rights notes, and versioning. Record duration, resolution, frame rate, audio tracks, and project references when metadata is available."),
    ("multimedia-production", "Coordinate video, audio, image, and caption deliverables.", "multimedia project, media production", "Define output formats, aspect ratios, accessibility requirements, source rights, and delivery milestones. Track asset dependencies and review checkpoints. Render only with available editing tools."),
    ("image-asset-pipeline", "Organize image generation, editing, export, and optimization.", "image pipeline, image assets", "Define source format, dimensions, color profile, transparent-background needs, naming, and export variants. Preserve masters and verify rendered assets at display size. Distinguish original assets from reference material."),
    ("design-handoff", "Prepare implementation-ready design specifications for developers.", "design handoff, Figma handoff", "Provide component states, spacing, typography, tokens, assets, breakpoints, and interaction notes. Record unresolved questions and edge cases. Ensure annotations match the approved design, not outdated mockups."),
    ("visual-regression-testing", "Detect unintended visual changes between UI builds.", "visual regression, screenshot compare", "Choose stable viewports and deterministic test data. Capture baseline and candidate screenshots under equivalent conditions. Review diffs for meaningful layout changes and avoid treating dynamic content as regressions."),
    ("api-documentation", "Write accurate API references and usage examples.", "API documentation, OpenAPI, endpoint guide", "Derive method, path, auth, parameters, schemas, responses, errors, and rate limits from the real contract. Keep examples runnable and redact secrets. Mark unsupported behavior explicitly."),
    ("data-migration", "Plan and verify safe data migrations.", "data migration, database migration", "Define source and target schemas, transformation rules, validation, backup, downtime, and rollback. Use dry runs and row-count checks. Preserve auditability and do not delete source data before verification."),
    ("schema-evolution", "Manage backward-compatible changes to data and API schemas.", "schema evolution, schema compatibility", "Identify consumers and compatibility requirements. Plan additive changes, dual-read/write periods, deprecation, and rollback. Validate old and new versions with contract tests."),
    ("database-backup-planning", "Design and verify database backup and restore procedures.", "database backup, recovery plan", "Define RPO/RTO, backup frequency, encryption, retention, and offsite copies. Test restores in an isolated environment. Document ownership, monitoring, and failure escalation."),
    ("cloud-cost-review", "Analyze cloud usage and find cost-saving opportunities.", "cloud cost, FinOps, cloud spend", "Map services, usage, commitments, storage, and egress. Separate variable and fixed costs. Recommend rightsizing and lifecycle policies with reliability trade-offs and measurable savings estimates."),
    ("reliability-engineering", "Improve service reliability using failure analysis and SLOs.", "SRE, reliability, SLO", "Define user-facing SLIs and SLOs. Analyze incidents, saturation, dependencies, and error budgets. Prioritize resilience work based on impact and verify recovery behavior through safe tests."),
    ("disaster-recovery", "Design disaster recovery strategy and restore exercises.", "disaster recovery, DR plan", "Identify critical systems, data, dependencies, RPO/RTO, and recovery order. Define alternate infrastructure, contacts, and validation checks. Run tabletop and restore exercises and track gaps."),
    ("sre-runbook", "Create actionable runbooks for site reliability operations.", "SRE runbook, on-call procedure", "State symptoms, impact, dashboards, safe diagnostic commands, mitigations, verification, escalation, and rollback. Warn about destructive steps and keep instructions synchronized with deployment topology."),
    ("customer-feedback-analysis", "Synthesize customer comments into evidence-backed themes.", "customer feedback, review analysis", "Deduplicate feedback, preserve source context, and categorize requests, pain, and praise. Quantify only the supplied sample. Separate frequency from severity and avoid treating vocal users as representative."),
    ("churn-analysis", "Analyze customer churn patterns and retention opportunities.", "churn, retention analysis", "Define churn event, cohort, period, and customer segment. Check missing data and denominator choices. Compare retention curves and possible drivers without asserting causation from correlation."),
    ("survey-design", "Create neutral surveys with clear response scales.", "survey questions, questionnaire design", "Clarify research objective and population. Use neutral wording, one concept per question, balanced options, and appropriate scales. Minimize sensitive data and plan analysis before fielding."),
    ("pricing-research", "Research willingness to pay and pricing perceptions.", "pricing research, willingness to pay", "Define segments and value metric. Choose interviews, survey, or behavioral evidence. Avoid leading questions and explain sampling limits. Compare willingness-to-pay evidence with costs and alternatives."),
    ("product-analytics", "Define product metrics and interpret user behavior.", "product analytics, funnel metrics", "Map product goals to activation, engagement, retention, and guardrail metrics. Define event names and properties consistently. Check instrumentation, cohort definitions, privacy, and confounding factors."),
    ("technical-support", "Diagnose technical issues with clear, safe troubleshooting steps.", "technical support, troubleshoot device, technical problem", "Confirm symptoms, environment, recent changes, and impact. Give reversible checks first, preserve evidence, and avoid requesting passwords or secret tokens. Escalate destructive or account-specific actions to an authorized operator."),
    ("help-center-design", "Organize a searchable self-service help center.", "help center, FAQ site, knowledge articles", "Group articles around user tasks and vocabulary. Define templates, categories, search terms, ownership, update cadence, and escalation. Keep article steps tested against the current product."),
    ("knowledge-management", "Create a maintainable system for capturing and reusing team knowledge.", "knowledge management, internal wiki", "Define content types, metadata, owners, review dates, and access rules. Capture decisions and procedures close to their source. Remove duplicates and mark stale or uncertain information."),
    ("technical-support-playbooks", "Create repeatable support guides for common technical issues.", "support playbook, troubleshooting guide", "For each issue define symptoms, impact, diagnostic questions, safe steps, expected result, rollback, and escalation. Use tested instructions and state when a fix requires elevated permissions."),
    ("ecommerce-operations", "Plan and improve day-to-day ecommerce workflows.", "ecommerce operations, online store process", "Map catalog, inventory, checkout, fulfillment, refunds, and customer support. Identify handoffs and failure states. Track order accuracy, delivery, cancellations, and returns using verified data."),
    ("product-catalog-management", "Maintain accurate and consistent product catalog records.", "product catalog, SKU management", "Define required attributes, identifiers, variants, taxonomy, images, pricing source, and lifecycle status. Validate completeness and duplicate SKUs. Keep source-of-truth rules explicit."),
    ("inventory-analysis", "Analyze stock levels, turnover, and replenishment needs.", "inventory, stock analysis, reorder point", "Check units, locations, time period, lead time, and demand assumptions. Identify slow movers, stockouts, and safety-stock needs. Separate measured demand from forecast estimates."),
    ("order-fulfillment", "Design reliable order picking, packing, and shipment workflows.", "order fulfillment, packing workflow", "Map order states, inventory reservations, picking, packing, carrier handoff, tracking, and exceptions. Include verification checkpoints and escalation for missing or damaged items."),
    ("customer-retention", "Design retention initiatives using evidence about customer needs.", "customer retention, loyalty strategy", "Identify churn points, cohort behavior, and customer feedback. Design relevant lifecycle touchpoints and measurable experiments. Avoid manipulative dark patterns or unsupported uplift claims."),
    ("community-management", "Plan healthy community operations and moderation workflows.", "community management, Discord community", "Define norms, moderation tiers, escalation, member onboarding, and feedback channels. Apply rules consistently and protect member privacy. Track health using meaningful indicators, not activity alone."),
    ("gameplay-design", "Design game mechanics and progression systems around player goals.", "game design, gameplay mechanics", "Define player fantasy, core loop, feedback, progression, balance, and fail states. Test clarity and exploitability. Document tuning variables and how changes affect player types."),
    ("game-economy-design", "Balance in-game currencies, sinks, rewards, and progression.", "game economy, virtual currency balance", "Map currency sources and sinks, reward rates, progression gates, and player segments. Model inflation and farming exploits. Use simulations or telemetry where available; label assumptions otherwise."),
    ("game-performance-review", "Review game scripts and scenes for performance risks.", "game optimization, game lag, Roblox performance", "Profile before optimizing. Inspect update loops, allocations, network traffic, rendering, and event connections. Prioritize measured bottlenecks and verify on target devices, including low-end hardware."),
    ("gameplay-testing", "Create structured tests for gameplay mechanics and progression.", "game testing, gameplay QA", "Define scenarios, starting state, expected outcomes, edge cases, and multiplayer conditions. Record reproducible steps, runtime, and severity. Retest fixes and regression paths."),
    ("game-publishing", "Prepare a game for a controlled public release.", "publish game, game release checklist", "Verify build, platform requirements, metadata, content ratings, permissions, analytics, support channels, and rollback. Do not claim submission or publication until the platform confirms it."),
    ("release-coordination", "Coordinate multi-team release activities and dependencies.", "release coordinator, release planning", "Define scope, owners, dependency dates, freeze windows, acceptance checks, communications, and rollback criteria. Track blockers and confirm each gate from authoritative status."),
    ("change-management", "Plan safe operational and organizational changes.", "change management, change request", "Describe reason, scope, impact, risk, approvals, implementation, verification, rollback, and communication. Keep approval requirements explicit and distinguish approved changes from proposals."),
    ("training-material-design", "Build structured training materials for a target audience.", "training guide, learning materials", "Define learner level, objective, prerequisites, practice, and assessment. Use examples from the actual workflow. Break material into teachable units and validate with a pilot learner."),
    ("technical-onboarding", "Create onboarding paths for new developers or technical users.", "developer onboarding, technical onboarding", "Document access, environment setup, architecture, conventions, first task, testing, and help channels. Verify every command in a clean environment and mark account-dependent steps."),
    ("team-process-design", "Improve team workflows, roles, handoffs, and decision practices.", "team process, workflow design", "Map work intake, prioritization, execution, review, and escalation. Identify bottlenecks and unclear ownership. Propose lightweight agreements with measurable review points."),
    ("meeting-facilitation", "Run focused meetings that end with clear decisions and owners.", "facilitate meeting, meeting agenda", "Define desired outcome and decision-maker. Send a focused agenda, timebox topics, invite relevant voices, and capture decisions, action owners, and deadlines only when agreed."),
    ("negotiation-preparation", "Prepare evidence-based negotiation goals and fallback positions.", "negotiation strategy, negotiate contract", "Clarify interests, constraints, alternatives, priorities, and authority. Separate must-haves from tradeable terms. Prepare objective evidence, questions, and respectful fallback options."),
    ("customer-success-planning", "Create measurable customer success plans and adoption milestones.", "customer success, onboarding plan", "Define customer outcomes, stakeholders, baseline, adoption milestones, risks, and review cadence. Track verified usage and value indicators. Avoid promising outcomes outside the team's control."),
    ("service-level-design", "Define measurable service commitments and escalation rules.", "SLA, service level, uptime target", "Specify availability measurement, time window, exclusions, support response targets, severity definitions, and reporting. Align commitments with actual capacity and monitoring evidence."),
    ("quality-management", "Establish quality plans, corrective actions, and continuous improvement.", "quality management, QA process", "Define quality objectives, acceptance criteria, inspections, issue classification, corrective actions, and audit evidence. Measure recurring defects and verify corrective actions prevent recurrence."),
    ("api-security-review", "Review API authentication, authorization, input validation, and data exposure.", "API security review, secure API", "Map endpoints, identities, roles, data sensitivity, and trust boundaries. Check authentication, authorization, rate limits, validation, error leakage, and secret handling. Rank concrete findings and include safe reproduction steps."),
    ("dependency-management", "Maintain healthy dependencies, versions, licenses, and update policy.", "dependency update, package maintenance", "Inventory direct and transitive dependencies. Check support status, vulnerabilities, licensing, and compatibility. Plan controlled upgrades with lockfiles, tests, rollback, and change notes."),
    ("code-migration", "Plan and execute safe migrations between languages, frameworks, or versions.", "code migration, framework upgrade", "Define source and target versions, compatibility gaps, scope, and behavior contracts. Migrate incrementally, preserve tests, compare outputs, and keep a rollback path. Flag generated or manual work separately."),
    ("refactoring", "Improve code structure while preserving externally visible behavior.", "refactor code, clean architecture", "Establish behavior with tests first. Identify duplication, coupling, unclear names, and oversized functions. Make small changes, preserve interfaces, and run regression tests after each step."),
    ("technical-debt-review", "Identify technical debt and prioritize repayment by impact.", "technical debt, code maintainability", "Record debt item, cause, affected areas, delivery or reliability cost, and remediation estimate. Prioritize by risk reduction and repeated friction, not code-style preference alone."),
    ("performance-budgeting", "Set measurable performance budgets for applications and pages.", "performance budget, page speed target", "Choose user-centered metrics, representative devices, and network conditions. Define budgets for bundle size, latency, memory, rendering, and startup. Add monitoring and regression gates."),
    ("game-content-planning", "Plan game content updates, events, and progression beats.", "game content plan, live ops", "Define player segments, event purpose, schedule, rewards, dependencies, and moderation needs. Check fairness and economy impact. Prepare fallback content and announce only verified dates."),
    ("live-ops-planning", "Plan safe recurring operations for a live game or digital service.", "live ops, game event schedule", "Create an event calendar, configuration checklist, monitoring plan, rollback, and player communications. Validate reward and eligibility rules before launch. Avoid unreviewed production changes."),
    ("game-monetization-review", "Review game monetization for clarity, fairness, and policy risks.", "game monetization, in-game purchases", "Map purchase value, price disclosure, random rewards, refunds, age context, and platform rules. Check whether progression pressures players unfairly. Flag legal/platform issues for specialist review."),
    ("game-community-strategy", "Build a sustainable strategy for player communities.", "gaming community, game Discord strategy", "Define community purpose, channels, onboarding, events, moderation, creator support, and feedback loop. Set safety boundaries and metrics for helpful participation and retention."),
    ("social-media-strategy", "Plan platform-specific social content around clear goals.", "social media strategy, social content", "Define audience, platform, objective, voice, content pillars, cadence, and measurement. Adapt format to platform norms and accessibility. Avoid engagement bait and unverified claims."),
    ("content-calendar", "Create an actionable multi-channel publishing calendar.", "content calendar, posting schedule", "Set goals, audiences, campaigns, channels, owners, deadlines, and asset dependencies. Balance formats and reuse thoughtfully. Include review, localization, and measurement checkpoints."),
    ("email-campaign-design", "Plan ethical email campaigns with clear segmentation and measurement.", "email campaign, newsletter strategy", "Define audience, consent basis, lifecycle stage, value proposition, subject, content, and CTA. Include unsubscribe and preference handling. Measure deliverability, engagement, and conversion responsibly."),
    ("lifecycle-marketing", "Design useful communications across the customer lifecycle.", "lifecycle marketing, onboarding emails", "Map signup, activation, adoption, renewal, and win-back moments. Trigger only on relevant user states and consent. Define suppression rules, frequency caps, and measurable outcomes."),
    ("growth-experiment-design", "Design responsible experiments to improve acquisition or activation.", "growth experiment, conversion experiment", "State the user problem, hypothesis, target metric, guardrails, sample, and duration. Avoid deceptive patterns. Predefine analysis and report uncertainty and segment effects."),
    ("brand-voice-development", "Define a consistent and recognizable written brand voice.", "brand voice, tone of voice", "Describe voice traits, audience, vocabulary, grammar, inclusivity, and examples across contexts. Distinguish stable voice from situational tone. Provide do/don't examples and a review checklist."),
    ("visual-content-strategy", "Plan visual content systems for social, web, and product channels.", "visual content, graphic content plan", "Define message, audience, channel dimensions, content formats, reusable templates, and rights. Keep visual hierarchy consistent and create accessibility alternatives such as alt text or captions."),
    ("localization-quality-review", "Review translated product content for locale correctness and consistency.", "localization QA, translation review", "Check glossary, placeholders, plural rules, date/number formats, tone, truncation, and locale conventions. Compare with source and test in-context layouts. Mark ambiguous source text for clarification."),
    ("customer-escalation", "Manage complex customer cases that need specialist ownership.", "customer escalation, support escalation", "Summarize verified facts, impact, troubleshooting already tried, urgency, and next owner. Protect personal data and secrets. Set a clear customer update cadence and record the resolution."),
    ("crisis-communications", "Prepare clear communications for high-impact incidents or reputational events.", "crisis communication, public statement", "Confirm facts, affected groups, authority, and approval path. Lead with impact and actions, avoid speculation, protect private details, and coordinate consistent updates across channels."),
    ("procurement-planning", "Structure procurement needs, sourcing, and approval workflows.", "procurement, sourcing plan", "Define business need, requirements, budget authority, evaluation criteria, conflict checks, privacy/security needs, and approval gates. Maintain a transparent audit trail and fair vendor process."),
    ("vendor-due-diligence", "Assess a vendor's operational, security, privacy, and financial fit.", "vendor due diligence, supplier assessment", "Gather verifiable evidence on security controls, data handling, uptime, support, subcontractors, financial stability, and exit. Separate verified documentation from vendor assertions and open gaps."),
    ("operations-analytics", "Measure operational processes and identify bottlenecks.", "operations analytics, process metrics", "Define throughput, cycle time, backlog, rework, service quality, and capacity. Validate source data and compare segments. Distinguish measured changes from seasonal or mix effects."),
    ("product-roadmapping", "Create outcome-based roadmaps that reflect evidence and capacity.", "product roadmap, roadmap planning", "Group initiatives by user or business outcome. Show confidence, dependencies, effort bands, and sequencing. Avoid false precision in dates and keep discovery separate from committed delivery."),
    ("user-feedback-triage", "Classify user feedback into actionable product signals.", "user feedback triage, feature request sorting", "Capture user goal, context, frequency in supplied evidence, severity, and current workaround. Deduplicate requests and link themes to product outcomes. Do not equate volume with importance automatically."),
]

def run_builtin(context, arguments):
    """Execute the built-in plugin matching context.plugin_id."""
    plugin_id = context.plugin_id
    handlers = {item[0]: item[4] for item in PLUGIN_DEFINITIONS}
    if plugin_id not in handlers:
        raise KeyError(f"unknown built-in plugin: {plugin_id}")
    args = dict(arguments or {})
    if plugin_id in {"files-list", "files-read", "files-write", "web-fetch", "image-dimensions", "file-checksum", "directory-size", "file-size-human", "file-find", "file-text-search", "duplicate-files", "directory-tree", "file-extension-count", "file-line-count", "file-head", "file-tail", "file-json-inspect", "archive-create", "archive-extract-safe", "file-copy", "file-rename", "directory-empty-check"}:
        return handlers[plugin_id](args, context)
    return handlers[plugin_id](args)


def install_builtin_catalog(plugin_root=None, skill_root=None):
    """Materialize all 200 plugins and 200 skills; never overwrite existing files."""
    import json as _json
    from pathlib import Path as _Path
    base = _Path(__file__).resolve().parent
    use_default_roots = plugin_root is None and skill_root is None
    plugins = _Path(plugin_root) if plugin_root is not None else base / "plugins" / "catalog"
    skills = _Path(skill_root) if skill_root is not None else base / "skills" / "catalog"
    if use_default_roots:
        plugins_ready = all((plugins / item[0] / "plugin.json").is_file() and (plugins / item[0] / "plugin.py").is_file() for item in PLUGIN_DEFINITIONS)
        skills_ready = all((skills / item[0] / "SKILL.md").is_file() and (skills / item[0] / "scripts" / "main.py").is_file() for item in SKILL_DEFINITIONS)
        if plugins_ready and skills_ready:
            return {"plugins": len(PLUGIN_DEFINITIONS), "skills": len(SKILL_DEFINITIONS),
                    "plugin_root": str(plugins), "skill_root": str(skills), "already_installed": True}
    plugins.mkdir(parents=True, exist_ok=True)
    skills.mkdir(parents=True, exist_ok=True)
    for plugin_id, name, description, keywords, handler in PLUGIN_DEFINITIONS:
        folder = plugins / plugin_id
        folder.mkdir(exist_ok=False)
        permissions = ["filesystem.read", "filesystem.write"] if plugin_id in {"archive-extract-safe", "file-copy"} else (["filesystem.read"] if plugin_id in {"files-list", "files-read", "image-dimensions", "file-checksum", "directory-size", "file-size-human", "file-find", "file-text-search", "duplicate-files", "directory-tree", "file-extension-count", "file-line-count", "file-head", "file-tail", "file-json-inspect", "directory-empty-check"} else (["filesystem.write"] if plugin_id in {"files-write", "archive-create", "file-rename"} else (["network.read"] if plugin_id == "web-fetch" else [])))
        manifest = {"id": plugin_id, "name": name, "version": "1.0.0", "description": description,
                    "entrypoint": "plugin.py", "capabilities": ["network-read"] if plugin_id == "web-fetch" else ["local-processing"],
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
    parser = argparse.ArgumentParser(description="Install Plug's 200 built-in plugins and 200 skills.")
    parser.add_argument("--install", action="store_true", help="materialize the bundled catalog")
    args = parser.parse_args()
    if args.install:
        print(json.dumps(install_builtin_catalog(), indent=2))
    else:
        parser.print_help()
