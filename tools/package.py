#!/usr/bin/env python3
"""Build a compact, self-contained Plug source ZIP distribution."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIMIT = 200 * 1024
INCLUDE_ROOT_FILES = ("README.md", "SECURITY.md", "pyproject.toml")


def package_files() -> list[Path]:
    files = [ROOT / name for name in INCLUDE_ROOT_FILES if (ROOT / name).is_file()]
    package = ROOT / "plug"
    for path in package.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def build(output: Path, limit: int) -> tuple[int, int, int]:
    files = package_files()
    plugin_count = sum(path.name == "plugin.json" for path in files)
    skill_count = sum(path.name == "SKILL.md" for path in files)
    if plugin_count != 200 or skill_count != 200:
        raise SystemExit(
            f"Catalog check failed: expected 200 plugins and 200 skills; "
            f"found {plugin_count} plugins and {skill_count} skills."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())

    with ZipFile(output) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise SystemExit(f"ZIP integrity check failed at: {bad_member}")

    size = output.stat().st_size
    if size > limit:
        output.unlink(missing_ok=True)
        raise SystemExit(
            f"ZIP is {size:,} bytes; limit is {limit:,} bytes. "
            "No oversized archive was kept."
        )
    return size, plugin_count, skill_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "Plug.zip")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    if args.max_bytes < 1:
        parser.error("--max-bytes must be positive")
    size, plugins, skills = build(args.output, args.max_bytes)
    print(f"Created {args.output}: {size:,}/{args.max_bytes:,} bytes")
    print(f"Included {plugins} plugins and {skills} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
