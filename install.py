#!/usr/bin/env python3
"""Safely restore the full Plug source tree from plug-source.tar.xz."""
from __future__ import annotations

import argparse
import tarfile
from pathlib import Path, PurePosixPath


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default="plug-source", help="restore destination (default: ./plug-source)")
    parser.add_argument("--force", action="store_true", help="allow extraction into a non-empty destination")
    args = parser.parse_args()

    archive_path = Path(__file__).resolve().with_name("plug-source.tar.xz")
    if not archive_path.is_file():
        parser.error("plug-source.tar.xz is missing; download it from the repository first")

    destination = Path(args.dest).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()) and not args.force:
        parser.error(f"{destination} is not empty; choose another --dest or pass --force")

    with tarfile.open(archive_path, "r:xz") as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            target = (destination / member.name).resolve()
            if name.is_absolute() or ".." in name.parts or not target.is_relative_to(destination):
                parser.error(f"unsafe archive path: {member.name}")
            if not member.isfile():
                parser.error(f"unsupported archive entry: {member.name}")
        archive.extractall(destination)

    print(f"Plug source restored to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
