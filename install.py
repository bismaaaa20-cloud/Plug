#!/usr/bin/env python3
"""Safely restore the full Plug source tree from plug-source.zip."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default="plug-source", help="restore destination (default: ./plug-source)")
    parser.add_argument("--force", action="store_true", help="allow extraction into a non-empty destination")
    args = parser.parse_args()

    archive_path = Path(__file__).resolve().with_name("plug-source.zip")
    if not archive_path.is_file():
        parser.error("plug-source.zip is missing; download it from the repository first")

    destination = Path(args.dest).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()) and not args.force:
        parser.error(f"{destination} is not empty; choose another --dest or pass --force")

    with ZipFile(archive_path) as archive:
        bad = archive.testzip()
        if bad:
            parser.error(f"archive integrity check failed at {bad}")
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination):
                parser.error(f"unsafe archive path: {member.filename}")
        archive.extractall(destination)

    print(f"Plug source restored to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
