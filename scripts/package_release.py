"""Sukuria švarų projekto šaltinio archyvą pateikimui."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

EXCLUDED_DIRS = {
    ".codex-work",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "instance",
    "node_modules",
    "output",
    "venv",
}
EXCLUDED_FILES = {
    ".coverage",
    ".env",
    "package_release.py",
}
EXCLUDED_SUFFIXES = {
    ".db",
    ".log",
    ".pyc",
    ".sqlite",
    ".sqlite3",
}


def should_include(relative: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if relative.name in EXCLUDED_FILES:
        return False
    if relative.name.startswith(".env.") and relative.name != ".env.example":
        return False
    return relative.suffix.lower() not in EXCLUDED_SUFFIXES


def package(project_root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file_path in sorted(project_root.rglob("*")):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(project_root)
            if should_include(relative):
                archive.write(file_path, Path("secure-wizard") / relative)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.project_root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
