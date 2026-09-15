#!/usr/bin/env python3
"""Check delivered knowledge files offline; never run commands from documents."""

from __future__ import annotations

import argparse
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


MANAGED_PREFIXES = ("docs/", "skills/", "example/", "proto/")
ENTRY_FILES = ("AGENTS.md", "CLAUDE.md", "docs/README.md", "example/README.md")


def check_context(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    def contained(path: Path) -> bool:
        return path.resolve() == root or root in path.resolve().parents

    manifest = root / "MANIFEST.txt"
    if not contained(manifest) or not manifest.is_file():
        return ["missing or escaping MANIFEST.txt"]
    entries = {line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()}
    for entry in sorted(entries):
        path = PurePosixPath(entry)
        if path.is_absolute() or ".." in path.parts or "\\" in entry:
            errors.append("unsafe MANIFEST entry")
            continue
        if entry.startswith("project-experience/"):
            errors.append("project experience must not be managed by MANIFEST.txt")
        if entry.startswith(MANAGED_PREFIXES):
            target = root / entry
            if not contained(target) or not target.is_file():
                errors.append(f"missing or escaping managed file: {entry}")

    # Website and runtime files have their own release checks. Optional local
    # project experience is intentionally neither read nor initialized here.
    documents = set(ENTRY_FILES)
    documents.update(entry for entry in entries if entry.endswith(".md") and entry.startswith(("docs/", "skills/")))
    for relative in sorted(documents):
        source = root / relative
        if not contained(source) or not source.is_file():
            errors.append(f"missing or escaping knowledge document: {relative}")
            continue
        if relative not in entries:
            errors.append(f"knowledge entry missing from MANIFEST: {relative}")
        content = source.read_text(encoding="utf-8")
        # Code examples can contain illustrative Markdown; check prose links.
        content = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", content)
        links = re.findall(r"\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\)", content)
        for link in links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = source.parent / unquote(url.path)
            if not contained(target):
                errors.append(f"link escapes delivery root: {relative}")
                continue
            target_name = target.resolve().relative_to(root).as_posix()
            if not target.exists():
                errors.append(f"missing link: {relative} -> {target_name}")
            elif target.is_file() and target_name.startswith(MANAGED_PREFIXES) and target_name not in entries:
                errors.append(f"linked file missing from MANIFEST: {target_name}")
        # Existing task-to-skill tables use inline code, not Markdown links.
        routes = re.findall(r"`(skills/[a-z0-9-]+/SKILL\.md)`", content) if relative in ("AGENTS.md", "docs/README.md") else []
        for skill in routes:
            target = root / skill
            if not contained(target) or not target.is_file() or skill not in entries:
                errors.append(f"unavailable routed skill: {relative} -> {skill}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="delivery directory (default: current directory)")
    args = parser.parse_args()
    try:
        errors = check_context(args.root)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL cannot inspect delivery knowledge ({type(exc).__name__})")
        return 2
    if errors:
        print("FAIL delivery knowledge")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS delivery knowledge files, local Markdown links and skill routes (static only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
