#!/usr/bin/env python3
"""Extract bounded, read-only LightESB log evidence; never emit arbitrary messages."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

sys.dont_write_bytecode = True

from log_io import Budget, DEFAULTS, EvidenceError, SafeRoot, relative_parts
from log_parse import layout_config, parse_record, records, safe_path, safe_text, timestamp
from log_json import ENDPOINTS, adapt, collection_metadata, strict_json

EXIT = {"COMPLETE_WITHIN_SCOPE": 0, "PARTIAL": 3, "UNAVAILABLE": 1, "INVALID_INPUT": 2}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise EvidenceError("INVALID_ARGUMENTS", "input")


def arguments(argv):
    parser = Parser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True, parser_class=Parser)
    for mode in ("inventory", "query", "import-json"):
        p = sub.add_parser(mode)
        p.add_argument("--root", required=mode != "import-json")
        p.add_argument("--root-alias", default="local")
        p.add_argument("--diagnosis-id", help="UUID for the same investigation; task names are not valid UUIDs")
        for name, default in DEFAULTS.items():
            p.add_argument("--max-" + name.replace("_", "-"), type=float if name == "seconds" else int, default=default)
        if mode == "import-json":
            p.add_argument("--kind", choices=tuple(ENDPOINTS), required=True)
            p.add_argument("--source", "--input", dest="source", required=True, help="Relative JSON file, or - for stdin")
            p.add_argument("--metadata", help="Small caller-supplied JSON collection metadata")
            p.add_argument("--timezone")
        if mode == "query":
            p.add_argument("--source", action="append", required=True)
            p.add_argument("--offset", type=int)
            p.add_argument("--length", type=int)
            p.add_argument("--expected-identity")
            p.add_argument("--gzip", action="store_true", help="Explicitly permit gzip; bounded forward decompression only")
            p.add_argument("--layout-config")
            p.add_argument("--timezone")
            p.add_argument("--service-name")
            p.add_argument("--service-version")
            p.add_argument("--level", action="append", choices=("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"))
            p.add_argument("--id")
            p.add_argument("--contains", help="Literal text filter; text is never echoed")
            p.add_argument("--start-time")
            p.add_argument("--end-time")
    return parser.parse_args(argv)


def new_result(mode="unknown", diagnosis=None):
    return dict(schemaVersion=1, diagnosisId=diagnosis or str(uuid.uuid4()), captureId=str(uuid.uuid4()),
                mode=mode, queriedAt=datetime.now(timezone.utc).isoformat(), status="COMPLETE_WITHIN_SCOPE",
                request={}, sources=[], events=[], coverage=dict(scanned=0, selected=0, read=0, skipped=0,
                recordsRead=0, layoutParsed=0, semanticRecognized=0, unclassified=0, suppressed=0,
                truncated=False, changedDuringRead=False, unknownFormat=False,
                timeWindowCoverage="READ_RANGES_ONLY", stopReasons=[]),
                usage=dict(inputBytes=0, decompressedBytes=0, decompressedBytesExact=True, outputBytes=0, elapsedMs=0), errors=[])


def partial(result, reason):
    if result["status"] != "INVALID_INPUT":
        result["status"] = "PARTIAL"
    result["coverage"]["truncated"] = True
    if reason not in result["coverage"]["stopReasons"]:
        result["coverage"]["stopReasons"].append(reason)


def source(result, relative, alias, kind="application-log"):
    safe = safe_path(relative)
    value = dict(sourceId="s" + str(len(result["sources"])+1), rootAlias=alias,
                 sourceKind=kind, state="SKIPPED", identityBefore=None, identityAfter=None,
                 ranges=[], bytesRead=0, pathSuppressed=safe is None, truncated=False,
                 changedDuringRead=False, readError=None, parseWarnings=[])
    if safe:
        value["file"] = safe
    else:
        value["inputAlias"] = value["sourceId"]
    result["sources"].append(value)
    return value


def add_error(result, exc, src=None):
    result["errors"].append(dict(code=exc.code, stage=exc.stage, sourceId=src["sourceId"] if src else None))
    if src:
        if src["state"] not in ("READ", "CHANGED"):
            result["coverage"]["skipped"] += 1
        src["readError"] = exc.code
        src["state"] = "MISSING" if exc.code == "FILE_MISSING" else "UNREADABLE"


def emit(result, limit):
    # outputBytes includes its own digits and the terminating newline.
    def encode():
        for _ in range(8):
            encoded = (json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n").encode("utf-8")
            if len(encoded) == result["usage"]["outputBytes"]:
                return encoded
            result["usage"]["outputBytes"] = len(encoded)
        raise RuntimeError("output size did not converge")
    payload = encode()
    while len(payload) > limit:
        partial(result, "OUTPUT_LIMIT")
        if result["events"]:
            result["events"].pop()
        elif result["sources"]:
            removed = result["sources"].pop()["sourceId"]
            result["errors"] = [error for error in result["errors"] if error["sourceId"] != removed]
        elif result["errors"]:
            result["errors"].pop()
        else:
            result["request"] = {}
        payload = encode()
    sys.stdout.buffer.write(payload)
    return EXIT[result["status"]]


def validate(args):
    if not safe_text(args.root_alias, "alias"):
        raise EvidenceError("INVALID_ALIAS", "input")
    if args.diagnosis_id:
        try:
            args.diagnosis_id = str(uuid.UUID(args.diagnosis_id))
        except (ValueError, AttributeError):
            raise EvidenceError("INVALID_DIAGNOSIS_ID", "input") from None
    if args.mode in ("query", "import-json") and args.timezone:
        try:
            ZoneInfo(args.timezone)
        except (ValueError, ZoneInfoNotFoundError):
            raise EvidenceError("INVALID_TIMEZONE", "input") from None
    if args.mode == "import-json":
        if args.source != "-":
            if not args.root:
                raise EvidenceError("ROOT_REQUIRED", "input")
            relative_parts(args.source)
        if args.metadata:
            if len(args.metadata.encode()) > 4096:
                raise EvidenceError("METADATA_LIMIT", "input")
        return
    if args.mode != "query":
        return
    for path in args.source + ([args.layout_config] if args.layout_config else []):
        relative_parts(path)
    if any(path.endswith(".gz") for path in args.source) and not args.gzip:
        raise EvidenceError("GZIP_REQUIRES_EXPLICIT_OPTION", "input")
    for value, kind in ((args.service_name, "service"), (args.service_version, "version"), (args.id, "id")):
        if value is not None and safe_text(value, kind) is None:
            raise EvidenceError("INVALID_FILTER", "input")
    if args.contains is not None and len(args.contains.encode()) > 1024:
        raise EvidenceError("FILTER_TOO_LONG", "input")
    for value in (args.start_time, args.end_time):
        if value and timestamp(value, args.timezone)[0] is None:
            raise EvidenceError("INVALID_TIME_FILTER", "input")
    if args.offset is not None and args.offset < 0 or args.length is not None and args.length <= 0:
        raise EvidenceError("INVALID_RANGE", "input")
    if args.start_time and args.end_time:
        start = timestamp(args.start_time, args.timezone)
        end = timestamp(args.end_time, args.timezone)
        a, b = datetime.fromisoformat(start[1] or start[0]), datetime.fromisoformat(end[1] or end[0])
        if (a.tzinfo is None) != (b.tzinfo is None) or a > b:
            raise EvidenceError("INVALID_TIME_RANGE", "input")
    if args.expected_identity:
        if len(args.expected_identity) > 512:
            raise EvidenceError("INVALID_IDENTITY", "input")
        try:
            expected = json.loads(args.expected_identity)
        except ValueError:
            raise EvidenceError("INVALID_IDENTITY", "input") from None
        if not isinstance(expected, dict) or set(expected) != {"device", "inode", "size", "mtimeNs"} or any(type(v) is not int or v < 0 for v in expected.values()):
            raise EvidenceError("INVALID_IDENTITY", "input")
        args.expected_identity = expected


def matches(event, raw, args):
    if args.level and event["level"] not in args.level:
        return False
    if args.service_name and event["serviceName"] != args.service_name:
        return False
    if args.service_version and event["serviceVersion"] != args.service_version:
        return False
    if args.id and args.id not in (event["routeId"], event["exchangeId"], event["instanceUuid"]):
        return False
    if args.contains is not None and args.contains.encode() not in raw:
        return False
    current = datetime.fromisoformat(event["normalizedTime"] or event["timestamp"])
    for bound, lower in ((args.start_time, True), (args.end_time, False)):
        if not bound:
            continue
        original, normalized = timestamp(bound, args.timezone)
        dt = datetime.fromisoformat(normalized or original)
        if (current.tzinfo is None) != (dt.tzinfo is None):
            raise EvidenceError("TIMEZONE_COMPARISON_UNKNOWN", "filter")
        if lower and current < dt or not lower and current > dt:
            return False
    return True


def bound_appenders(config, root, path):
    matches = []
    for app in config.values():
        if not app.get("referenced"):
            continue
        for key in ("fileName", "filePattern"):
            value = app.get(key)
            if not value or ".." in Path(value).parts:
                continue
            if Path(value).is_absolute():
                try:
                    value = Path(value).relative_to(root.path).as_posix()
                except ValueError:
                    continue
            # Match only known rolling tokens; never use config as a regex or
            # open a path derived from it.
            pattern = re.escape(value)
            pattern = pattern.replace(re.escape("%d{yyyy-MM-dd}"), r"\d{4}-\d{2}-\d{2}")
            pattern = pattern.replace(re.escape("%i"), r"\d+")
            if re.fullmatch(pattern, path):
                matches.append(app)
                break
    return matches


def query(root, args, budget, result):
    config, config_warnings = {}, []
    if args.layout_config:
        cfg = source(result, args.layout_config, args.root_alias, "layout-config")
        try:
            data, meta = root.read(args.layout_config, budget, offset=0)
            cfg.update(meta)
            cfg["state"] = "CHANGED" if meta["changedDuringRead"] else "READ"
            result["coverage"]["read"] += 1
            result["coverage"]["changedDuringRead"] |= meta["changedDuringRead"]
            if meta["truncated"] or meta["changedDuringRead"]:
                config_warnings = ["CONFIG_INCOMPLETE"]
            else:
                config, config_warnings = layout_config(data)
            cfg["parseWarnings"].extend(config_warnings)
        except EvidenceError as exc:
            add_error(result, exc, cfg)
            config_warnings = [exc.code]
        if config_warnings:
            partial(result, "LAYOUT_UNRESOLVED")
    paths = list(dict.fromkeys(args.source))
    result["coverage"]["selected"] = len(paths) + int(bool(args.layout_config))
    file_limit = max(0, budget.limits["files"] - int(bool(args.layout_config)))
    if len(paths) > file_limit:
        partial(result, "FILE_LIMIT")
        result["coverage"]["skipped"] += len(paths)-file_limit
    for index, path in enumerate(paths[:file_limit]):
        src = source(result, path, args.root_alias)
        try:
            if path.endswith(".gz") and not args.gzip:
                raise EvidenceError("GZIP_REQUIRES_EXPLICIT_OPTION", "input")
            data, meta = root.read(path, budget, args.offset, args.length, args.expected_identity, path.endswith(".gz"))
            src.update(meta)
            src["state"] = "CHANGED" if meta["changedDuringRead"] else "READ"
            src["layoutOrigin"] = "inferred"
            bound = bound_appenders(config, root, path)
            layouts = {app.get("layout") for app in bound}
            if not bound and args.layout_config:
                src["parseWarnings"].append("LAYOUT_NOT_BOUND")
            result["coverage"]["read"] += 1
            if meta["truncated"] or meta["changedDuringRead"]:
                partial(result, "SOURCE_INCOMPLETE")
            result["coverage"]["changedDuringRead"] |= meta["changedDuringRead"]
            if any(app.get("charset") == "unsupported" for app in bound):
                src["parseWarnings"].append("CONFIG_CHARSET_UNSUPPORTED")
                partial(result, "CONFIG_CHARSET_UNSUPPORTED")
                continue
            span = meta["ranges"][0]
            parse_start = span["start"]
            if parse_start > 0:
                # The slice may start inside a message that contains a fake
                # timestamp. Without its preceding byte, discard the first
                # physical line even if it resembles a complete record header.
                first_newline = data.find(b"\n")
                dropped = len(data) if first_newline < 0 else first_newline+1
                data, parse_start = data[dropped:], parse_start+dropped
                src["parseWarnings"].append("TRUNCATED_PREFIX")
                partial(result, "TRUNCATED_PREFIX")
            last_observed_key = None
            for raw, start, end, warning in records(data, parse_start, budget.limits["record_bytes"]):
                budget.check()
                result["coverage"]["recordsRead"] += 1
                if warning:
                    last_observed_key = None
                    if warning not in src["parseWarnings"]:
                        src["parseWarnings"].append(warning)
                    result["coverage"]["suppressed"] += 1
                    partial(result, "RECORD_INCOMPLETE")
                    continue
                parsed, warning = parse_record(raw, start, end, span["unit"], args.timezone, args.service_name, args.service_version)
                if warning:
                    last_observed_key = None
                    result["coverage"]["unknownFormat"] = True
                    result["coverage"]["unclassified"] += 1
                    result["coverage"]["suppressed"] += 1
                    if warning not in src["parseWarnings"]:
                        src["parseWarnings"].append(warning)
                    continue
                event, layout = parsed
                src["sourceKind"] = layout + "-log"
                if layouts == {layout}:
                    src["layoutOrigin"] = "configuration"
                if layouts and layout not in layouts:
                    if "LAYOUT_MISMATCH" not in src["parseWarnings"]:
                        src["parseWarnings"].append("LAYOUT_MISMATCH")
                    partial(result, "LAYOUT_MISMATCH")
                if args.timezone and event["normalizedTime"] is None:
                    if "AMBIGUOUS_LOCAL_TIME" not in src["parseWarnings"]:
                        src["parseWarnings"].append("AMBIGUOUS_LOCAL_TIME")
                cov = result["coverage"]
                cov["layoutParsed"] += 1
                recognized = event["signal"]["eventCode"] != "UNCLASSIFIED"
                cov["semanticRecognized"] += int(recognized)
                cov["unclassified"] += int(not recognized)
                cov["suppressed"] += int(event["suppressed"])
                keys = ("signal", "level", "logger", "serviceName", "serviceVersion", "routeId", "exchangeId")
                observed_key = tuple(json.dumps(event[k], sort_keys=True) for k in keys)
                consecutive = observed_key == last_observed_key
                last_observed_key = observed_key
                if not matches(event, raw, args):
                    last_observed_key = None
                    continue
                previous = result["events"][-1] if result["events"] else None
                keys = ("signal", "level", "logger", "serviceName", "serviceVersion", "routeId", "exchangeId")
                if recognized and consecutive and previous and previous["sourceId"] == src["sourceId"] and all(previous[k] == event[k] for k in keys):
                    previous["repeatCount"] = previous.get("repeatCount", 1) + 1
                    previous["lastLocator"] = event["locator"]
                    previous["lastTimestamp"] = event["timestamp"]
                    previous["suppressed"] |= event["suppressed"]
                    continue
                if len(result["events"]) >= budget.limits["events"]:
                    partial(result, "EVENT_LIMIT")
                    result["coverage"]["skipped"] += len(paths[:file_limit])-index-1
                    return
                event.update(sourceId=src["sourceId"], evidenceId="e"+str(len(result["events"])+1), repeatCount=1)
                result["events"].append(event)
        except EvidenceError as exc:
            add_error(result, exc, src)
            partial(result, exc.code)
            if exc.code in ("TIME_LIMIT", "BYTE_LIMIT"):
                result["coverage"]["skipped"] += len(paths[:file_limit])-index-1
                break
    if any(error["stage"] == "input" for error in result["errors"]):
        result["status"] = "INVALID_INPUT"
    elif result["coverage"]["read"] == 0 and result["errors"]:
        if not any(reason.endswith("_LIMIT") for reason in result["coverage"]["stopReasons"]):
            result["status"] = "UNAVAILABLE"


def main(argv=None):
    result = new_result()
    budget = None
    limit = DEFAULTS["output_bytes"]
    try:
        args = arguments(argv)
        validate(args)
        budget = Budget({name: getattr(args, "max_"+name) for name in DEFAULTS})
        limit = budget.limits["output_bytes"]
        result = new_result(args.mode, args.diagnosis_id)
        result["request"] = dict(limits=budget.limits, filters={}, timezone=getattr(args, "timezone", None))
        if args.mode == "query":
            result["request"]["filters"] = dict(serviceName=args.service_name, serviceVersion=args.service_version,
                levels=args.level, id=args.id, containsPresent=args.contains is not None,
                startTime=args.start_time, endTime=args.end_time)
        if args.mode == "import-json":
            import_json(args, budget, result)
        else:
            local_query(args, budget, result)
    except EvidenceError as exc:
        add_error(result, exc)
        result["status"] = "INVALID_INPUT" if exc.stage == "input" else "PARTIAL" if exc.code.endswith("_LIMIT") else "UNAVAILABLE"
    except (OSError, ValueError, TypeError, OverflowError):
        result["errors"].append(dict(code="PROCESSING_UNAVAILABLE", stage="process", sourceId=None))
        result["status"] = "UNAVAILABLE"
    if budget:
        result["usage"] = budget.usage()
    return emit(result, limit)


def local_query(args, budget, result):
    with SafeRoot(args.root) as root:
        if args.mode == "inventory":
            files, warnings = root.inventory(budget, Path(args.root).name)
            for item in files:
                src = source(result, item["file"], args.root_alias, "log-file")
                src.update(state="INVENTORIED", size=item["size"], observedModifiedNs=item["observedModifiedNs"])
            result["coverage"].update(scanned=budget.entries, selected=len(files))
            for warning in warnings:
                partial(result, warning)
        else:
            query(root, args, budget, result)


def import_json(args, budget, result):
    src = source(result, "stdin" if args.source == "-" else args.source, args.root_alias, args.kind)
    result["coverage"]["selected"] = 1
    result["request"]["kind"] = args.kind
    try:
        if args.metadata:
            metadata_bytes = args.metadata.encode()
            if len(metadata_bytes) > budget.remaining():
                raise EvidenceError("BYTE_LIMIT")
            budget.input_bytes += len(metadata_bytes)
            args.metadata = collection_metadata(strict_json(metadata_bytes, budget), args.kind)
        if args.source == "-":
            maximum = min(budget.limits["file_bytes"], budget.remaining())
            data = sys.stdin.buffer.read(maximum)
            budget.input_bytes += len(data)
            src.update(state="READ", bytesRead=len(data), ranges=[dict(start=0, end=len(data), unit="byte")], truncated=len(data) == maximum)
        else:
            with SafeRoot(args.root) as root:
                data, meta = root.read(args.source, budget, offset=0)
            src.update(meta)
            src["state"] = "CHANGED" if meta["changedDuringRead"] else "READ"
        result["coverage"]["read"] = 1
        result["coverage"]["changedDuringRead"] = src["changedDuringRead"]
        if src["truncated"] or src["changedDuringRead"]:
            partial(result, "JSON_SOURCE_INCOMPLETE")
            return
        document = strict_json(data, budget)
        if args.metadata:
            result["request"]["metadata"] = args.metadata
            if args.metadata.get("exitCode") not in (None, 0) and document.get("success") is not False:
                result["status"] = "UNAVAILABLE"
                result["errors"].append(dict(code="CLI_EXIT_FAILURE", stage="collect", sourceId=src["sourceId"]))
                return
        metadata, warnings, events = adapt(document, args.kind, budget, args.timezone)
        src.update(metadata)
        for reason in warnings:
            partial(result, reason)
        result["coverage"]["changedDuringRead"] |= any(row.get("changedDuringRead") is True for row in metadata.get("remoteFiles", []))
        for item in events:
            budget.check()
            cov = result["coverage"]
            cov["recordsRead"] += 1
            recognized = item["signal"]["eventCode"] != "UNCLASSIFIED"
            layout_parsed = item.pop("_layoutParsed", True)
            cov["layoutParsed"] += int(layout_parsed)
            cov["semanticRecognized"] += int(recognized)
            cov["unclassified"] += int(not recognized)
            cov["suppressed"] += int(item["suppressed"])
            cov["unknownFormat"] |= not layout_parsed
            if item["incomplete"]:
                partial(result, "RECORD_INCOMPLETE")
            if len(result["events"]) >= budget.limits["events"]:
                partial(result, "EVENT_LIMIT")
                break
            item.update(sourceId=src["sourceId"], evidenceId="e"+str(len(result["events"])+1))
            result["events"].append(item)
        if metadata.get("collectionFailed"):
            result["status"] = "UNAVAILABLE"
            result["errors"].append(dict(code="CLI_COLLECTION_FAILED", stage="collect", sourceId=src["sourceId"]))
    except EvidenceError as exc:
        add_error(result, exc, src)
        if exc.stage == "input":
            result["status"] = "INVALID_INPUT"
        elif exc.code.endswith("_LIMIT"):
            partial(result, exc.code)
        else:
            result["status"] = "UNAVAILABLE"


if __name__ == "__main__":
    raise SystemExit(main())
