#!/usr/bin/env python3
"""Offline comparison of an entire delivered context against a pinned baseline."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import zipfile

BASELINE = "delivery-context-baseline.json"
PREFIXES = ("docs/", "skills/", "example/", "proto/")
OWNED = ("AGENTS.md", "CLAUDE.md", "README.md", "MANIFEST.txt")
ORIGIN = "https://github.com/nghxni/lightesb-camel.git"


def safe_path(name):
    path = PurePosixPath(name)
    if (not name or name == "." or path.is_absolute() or path.as_posix() != name
            or any(part in (".", "..") for part in path.parts)
            or "\\" in name or any(ord(c) < 32 for c in name)):
        raise ValueError("unsafe context path")
    return name


def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(1 << 20), b""):
        value.update(block)
    return value.hexdigest()


def describe(path, root):
    if path.is_symlink() or root.resolve() not in path.resolve().parents or not path.is_file():
        raise ValueError("context file missing or escapes package: " + path.relative_to(root).as_posix())
    with path.open("rb") as stream:
        sha = digest(stream)
    return {"sha256": sha, "mode": "100755" if path.stat().st_mode & 0o111 else "100644"}


def load_baseline(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data) != {"schemaVersion", "kind", "official", "files"} or data["schemaVersion"] != 1 or data["kind"] != "lightesb-delivery-context":
        raise ValueError("invalid context baseline")
    official = data["official"]
    if set(official) != {"repository", "commit", "tree", "manifestSha256"} or official["repository"] != ORIGIN:
        raise ValueError("invalid official context identity")
    for key in ("commit", "tree"):
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", official[key]):
            raise ValueError("invalid official " + key)
    if not re.fullmatch(r"[0-9a-f]{64}", official["manifestSha256"]):
        raise ValueError("invalid official manifest digest")
    if not isinstance(data["files"], dict) or not data["files"]:
        raise ValueError("empty context baseline")
    for name, expected in data["files"].items():
        safe_path(name)
        if not name.startswith(PREFIXES) or set(expected) != {"sha256", "mode"}:
            raise ValueError("invalid managed context entry")
        if expected["mode"] not in ("100644", "100755") or not re.fullmatch(r"[0-9a-f]{64}", expected["sha256"]):
            raise ValueError("invalid managed context digest/mode")
    return data


def manifest_bytes(data):
    return ("\n".join(sorted([*data["files"], *OWNED, BASELINE])) + "\n").encode()


def expected_files(root):
    root = root.resolve()
    describe(root / BASELINE, root)
    data = load_baseline(root / BASELINE)
    expected = dict(data["files"])
    # These belong to the packaging repo. Compare archive bytes against that
    # repo, never replace its policies with the public repository's versions.
    for name in (*OWNED, BASELINE):
        expected[name] = describe(root / name, root)
    if (root / "MANIFEST.txt").read_bytes() != manifest_bytes(data):
        raise ValueError("packaging MANIFEST does not match cumulative baseline")
    return data, expected


def verify(root, archive=None):
    root = root.resolve()
    data, expected = expected_files(root)
    actual = {}
    for prefix in PREFIXES:
        directory = root / prefix
        if directory.is_symlink():
            raise ValueError("managed directory is a symlink")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError("symlink in managed context")
            if path.is_file():
                actual[path.relative_to(root).as_posix()] = describe(path, root)
    if set(actual) != set(data["files"]):
        raise ValueError("managed file set differs: missing=%s extra=%s" % (
            sorted(set(data["files"]) - set(actual)), sorted(set(actual) - set(data["files"]))))
    for name, descriptor in actual.items():
        if descriptor != expected[name]:
            raise ValueError("context content or mode differs: " + name)
    if archive is not None:
        verify_archive(archive, expected)
    return {"officialCommit": data["official"]["commit"], "filesChecked": len(actual)}


def verify_archive(path, expected):
    found = {}
    seen = set()

    def member(name, regular, mode, stream):
        relative = name.removeprefix("lightesb-camel/")
        if name == "lightesb-camel" and not regular:
            return
        safe_path(relative)
        if relative == name or relative in seen:
            raise ValueError("invalid or duplicate archive member")
        seen.add(relative)
        if not regular:
            return
        if relative in expected or relative.startswith(PREFIXES):
            if relative not in expected:
                raise ValueError("unexpected managed archive file: " + relative)
            found[relative] = {"sha256": digest(stream), "mode": "100755" if mode & 0o111 else "100644"}

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ValueError("unsupported archive file type")
                with archive.open(entry) as stream:
                    member(entry.filename.rstrip("/"), not entry.is_dir(), mode, stream)
    else:
        with tarfile.open(path, "r:gz") as archive:
            for entry in archive:
                if not entry.isfile() and not entry.isdir():
                    raise ValueError("unsupported archive file type")
                if entry.isfile():
                    with archive.extractfile(entry) as stream:
                        member(entry.name.rstrip("/"), True, entry.mode, stream)
                else:
                    member(entry.name.rstrip("/"), False, entry.mode, None)
    if found != expected:
        raise ValueError("archive context missing or differs: " + ", ".join(sorted(name for name in expected if found.get(name) != expected[name])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.root, args.archive)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, tarfile.TarError) as exc:
        parser.exit(1, "FAIL context baseline: %s\n" % exc)
    print("PASS cumulative context: %s files, official=%s" % (result["filesChecked"], result["officialCommit"]))


if __name__ == "__main__":
    main()
