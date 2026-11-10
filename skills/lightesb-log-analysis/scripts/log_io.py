"""Bounded directory-relative input. No networking or interpretation of inputs."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import stat
import time
import zlib


class EvidenceError(Exception):
    def __init__(self, code, stage="read"):
        self.code, self.stage = code, stage
        super().__init__(code)


DEFAULTS = dict(entries=2000, files=20, file_bytes=262144, bytes=8388608,
                record_bytes=16384, events=100, output_bytes=131072, seconds=10)
MAXIMUMS = dict(entries=10000, files=100, file_bytes=2097152, bytes=67108864,
                record_bytes=65536, events=500, output_bytes=524288, seconds=60)


class Budget:
    def __init__(self, limits=None):
        self.limits = dict(DEFAULTS)
        self.limits.update(limits or {})
        for key, value in self.limits.items():
            if key not in MAXIMUMS or not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 < value <= MAXIMUMS[key]:
                raise EvidenceError("INVALID_BUDGET", "input")
        if self.limits["output_bytes"] < 4096:
            raise EvidenceError("OUTPUT_BUDGET_TOO_SMALL", "input")
        self.started = time.monotonic()
        self.input_bytes = self.decompressed_bytes = self.entries = 0
        self.decompression_exact = True

    def check(self):
        if time.monotonic() - self.started >= self.limits["seconds"]:
            raise EvidenceError("TIME_LIMIT")

    def remaining(self):
        self.check()
        return max(0, self.limits["bytes"] - self.input_bytes - self.decompressed_bytes)

    def entry(self):
        self.check()
        if self.entries >= self.limits["entries"]:
            raise EvidenceError("ENTRY_LIMIT", "inventory")
        self.entries += 1

    def usage(self):
        return dict(inputBytes=self.input_bytes, decompressedBytes=self.decompressed_bytes,
                    decompressedBytesExact=self.decompression_exact, outputBytes=0, elapsedMs=round((time.monotonic() - self.started) * 1000))


def identity(st):
    return dict(device=st.st_dev, inode=st.st_ino, size=st.st_size, mtimeNs=st.st_mtime_ns)


def relative_parts(path):
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        raise EvidenceError("INVALID_PATH", "input")
    parts = path.split("/")
    if PurePosixPath(path).is_absolute() or any(p in ("", ".", "..") for p in parts):
        raise EvidenceError("INVALID_PATH", "input")
    return parts


class SafeRoot:
    def __init__(self, root):
        if not all(hasattr(os, k) for k in ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")) or os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd or os.scandir not in os.supports_fd:
            raise EvidenceError("SAFE_BACKEND_UNAVAILABLE", "open")
        # Walk from / instead of resolving symlinks before checking containment.
        absolute = os.path.abspath(os.fspath(root))
        if ".." in Path(root).parts:
            raise EvidenceError("INVALID_ROOT", "input")
        self.path = Path(absolute)
        self.fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in Path(absolute).parts[1:]:
                new_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd)
                os.close(self.fd)
                self.fd = new_fd
        except OSError:
            self.close()
            raise EvidenceError("ROOT_UNAVAILABLE", "open") from None

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def directory(self, parts):
        fd = os.dup(self.fd)
        try:
            for part in parts:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            return fd
        except OSError:
            os.close(fd)
            raise EvidenceError("DIRECTORY_UNAVAILABLE", "open") from None

    def still_bound(self, parts, parent):
        try:
            with SafeRoot(self.path) as current:
                a, b = os.fstat(self.fd), os.fstat(current.fd)
                if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                    return False
                reopened = current.directory(parts)
                try:
                    a, b = os.fstat(parent), os.fstat(reopened)
                    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)
                finally:
                    os.close(reopened)
        except (EvidenceError, OSError):
            return False

    def read(self, path, budget, offset=None, length=None, expected=None, gzip=False):
        parts = relative_parts(path)
        parent = self.directory(parts[:-1])
        fd = None
        try:
            before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode):
                raise EvidenceError("NOT_REGULAR_FILE", "open")
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            opened = os.fstat(fd)
            if identity(opened) != identity(before):
                raise EvidenceError("FILE_CHANGED", "open")
            if expected is not None and identity(opened) != expected:
                raise EvidenceError("IDENTITY_MISMATCH", "open")
            maximum = min(budget.limits["file_bytes"], budget.remaining())
            if maximum <= 0:
                raise EvidenceError("BYTE_LIMIT")
            if offset is not None and offset < 0 or length is not None and length <= 0:
                raise EvidenceError("INVALID_RANGE", "input")
            if gzip and offset is not None:
                raise EvidenceError("GZIP_RANDOM_ACCESS_UNSUPPORTED", "input")
            start = 0 if gzip else (max(0, opened.st_size - maximum) if offset is None else offset)
            if start > opened.st_size:
                raise EvidenceError("RANGE_OUTSIDE_FILE", "input")
            size = min(maximum, length if length is not None else maximum, opened.st_size - start)
            os.lseek(fd, start, os.SEEK_SET)
            chunks = []
            taken = 0
            while taken < size:
                budget.check()
                chunk = os.read(fd, min(16384, size - taken, budget.remaining()))
                if not chunk:
                    break
                budget.input_bytes += len(chunk)
                taken += len(chunk)
                chunks.append(chunk)
            after = os.fstat(fd)
            named_after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            changed = identity(opened) != identity(after) or identity(after) != identity(named_after) or not self.still_bound(parts[:-1], parent)
            data = b"".join(chunks)
            result = dict(identityBefore=identity(opened), identityAfter=identity(after),
                          bytesRead=taken, changedDuringRead=changed, truncated=start > 0 or start + taken < opened.st_size,
                          ranges=[dict(start=start, end=start+taken, unit="byte")], readError=None,
                          parseWarnings=[])
            if changed:
                result["parseWarnings"].append("FILE_CHANGED")
                return b"", result
            if gzip:
                decoder = zlib.decompressobj(31)
                limit = min(budget.limits["file_bytes"], budget.remaining())
                if limit <= 0:
                    result["truncated"] = True
                    result["parseWarnings"].append("BYTE_LIMIT")
                    return b"", result
                compressed, expanded, produced = data, [], 0
                while compressed and produced < limit:
                    budget.check()
                    allowance = min(8192, limit-produced, budget.remaining())
                    if allowance <= 0:
                        break
                    # Reserve the maximum output before entering zlib: a CRC
                    # failure may throw without returning already-expanded data.
                    budget.decompressed_bytes += allowance
                    try:
                        chunk = decoder.decompress(compressed, allowance)
                    except zlib.error:
                        budget.decompression_exact = False
                        raise EvidenceError("INVALID_GZIP", "decode") from None
                    budget.decompressed_bytes -= allowance-len(chunk)
                    expanded.append(chunk)
                    produced += len(chunk)
                    compressed = decoder.unconsumed_tail
                    if decoder.eof:
                        break
                data = b"".join(expanded)
                result["truncated"] = result["truncated"] or not decoder.eof or bool(decoder.unused_data)
                if result["truncated"]:
                    result["parseWarnings"].append("GZIP_PARTIAL")
                result["ranges"] = [dict(start=0, end=len(data), unit="decompressed-byte")]
            return data, result
        except FileNotFoundError:
            raise EvidenceError("FILE_MISSING", "open") from None
        except OSError:
            raise EvidenceError("FILE_UNREADABLE", "read") from None
        finally:
            if fd is not None:
                os.close(fd)
            os.close(parent)

    def inventory(self, budget, root_name=""):
        """List managed layouts; count all encountered entries without body reads."""
        found, warnings = [], []

        def walk(parts, role):
            fd = self.directory(parts)
            try:
                with os.scandir(fd) as entries:
                    for entry in entries:
                        budget.entry()
                        try:
                            st = entry.stat(follow_symlinks=False)
                        except OSError:
                            warnings.append("ENTRY_UNREADABLE")
                            continue
                        relative = "/".join(parts + [entry.name])
                        if stat.S_ISLNK(st.st_mode):
                            warnings.append("SYMLINK_SKIPPED")
                        elif stat.S_ISREG(st.st_mode) and role in ("root", "logs") and entry.name.endswith(".log"):
                            found.append(dict(file=relative, size=st.st_size, observedModifiedNs=st.st_mtime_ns))
                        elif stat.S_ISDIR(st.st_mode):
                            child_role = None
                            if role == "root" and entry.name == "logs":
                                child_role = "logs"
                            elif role == "root" and entry.name == "lightesb-camel-app":
                                child_role = "services"
                            elif role == "services":
                                child_role = "versions"
                            elif role == "versions":
                                child_role = "service-version"
                            elif role == "service-version" and entry.name == "logs":
                                child_role = "logs"
                            if child_role:
                                try:
                                    walk(parts + [entry.name], child_role)
                                except EvidenceError as exc:
                                    if exc.code in ("TIME_LIMIT", "ENTRY_LIMIT"):
                                        raise
                                    warnings.append(exc.code)
            finally:
                os.close(fd)
        try:
            walk([], "services" if root_name == "lightesb-camel-app" else "root")
        except EvidenceError as exc:
            warnings.append(exc.code)
        found.sort(key=lambda x: x["file"])
        if len(found) > budget.limits["files"]:
            warnings.append("FILE_LIMIT")
        return found[:budget.limits["files"]], sorted(set(warnings))
