"""Strict offline adapters for declared control-plane JSON kinds."""
from __future__ import annotations

import json
import math
import re

from log_io import EvidenceError
from log_parse import parse_record, safe_filekey, safe_path, safe_text, timestamp

ENDPOINTS = {
    "log-snapshot": "/api/logging/snapshot",
    "instance-list": "/api/instance-logs/v1/page",
    "instance-detail": "/api/instance-logs/v1/detail",
    "diagnostics-snapshot": "/api/diagnostics/runtime-snapshot",
    "diagnostics-warnings": "/api/diagnostics/runtime-snapshot",
    "route-status": "/api/routes/status",
    "route-detail": "/api/routes/{fileKey}/details",
    "deploy-status": "/api/deployment/status/{deploymentId}",
}
INSTANCE_STATES = {"SUCCESS", "FAILED", "FAIL", "ERROR", "RUNNING", "PROCESSING", "STARTED", "FINISHED", "UNKNOWN"}
DEPLOY_STATES = {"PENDING", "UPLOADING", "EXTRACTING", "VALIDATING", "BACKING_UP", "DEPLOYING", "LOADING_ROUTES", "SUCCESS", "FAILED", "ROLLED_BACK", "ROLLBACK_FAILED"}


def require(condition):
    if not condition:
        raise EvidenceError("JSON_KIND_MISMATCH", "input")


def strict_json(data, budget=None):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise EvidenceError("JSON_DUPLICATE_KEY", "input")
            out[key] = value
        return out
    def invalid_constant(value):
        raise EvidenceError("JSON_NONFINITE", "input")
    try:
        text = data.decode("utf-8", errors="strict")
        depth, quoted, escaped = 0, False, False
        for index, char in enumerate(text):
            if budget and index % 4096 == 0:
                budget.check()
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 32:
                    raise EvidenceError("JSON_STRUCTURE_LIMIT", "input")
            elif char in "]}":
                depth -= 1
        parsed = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise EvidenceError("INVALID_JSON", "input") from None
    pending, nodes = [(parsed, 0)], 0
    while pending:
        if budget:
            budget.check()
        item, depth = pending.pop()
        nodes += 1
        if nodes > 20000 or depth > 32:
            raise EvidenceError("JSON_STRUCTURE_LIMIT", "input")
        if isinstance(item, dict):
            pending.extend((key, depth+1) for key in item)
            pending.extend((value, depth+1) for value in item.values())
        elif isinstance(item, list):
            pending.extend((value, depth+1) for value in item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise EvidenceError("JSON_NONFINITE", "input")
        elif isinstance(item, str) and any(0xD800 <= ord(ch) <= 0xDFFF for ch in item):
            raise EvidenceError("JSON_INVALID_UNICODE", "input")
    require(isinstance(parsed, dict))
    return parsed


def integer(value):
    return value if type(value) is int and 0 <= value <= 2**53-1 else None


def metric(value):
    return value if type(value) in (int, float) and 0 <= value <= 2**53-1 and math.isfinite(value) else None


def boolean(value):
    return value if type(value) is bool else None


def enum(*values):
    return lambda value: value if isinstance(value, str) and value in values else None


def instance_status(value):
    if type(value) is int:
        value = str(value)
    return value if isinstance(value, str) and (value in INSTANCE_STATES or re.fullmatch(r"[0-9]{1,8}", value)) else None


def error_code(value):
    return value if safe_text(value) and len(value) <= 64 and re.fullmatch(r"[A-Z0-9_.-]+", value) else None


def time_value(value):
    return timestamp(value)[0]


def project(raw, converters):
    out, suppressed = {}, bool(set(raw)-set(converters))
    for key, convert in converters.items():
        if key in raw:
            value = raw[key]
            out[key] = convert(value) if value is not None else None
            suppressed |= value is not None and out[key] is None
    return out, suppressed


IDENTITIES = dict(serviceName=lambda v: safe_text(v, "service"), serviceVersion=lambda v: safe_text(v, "version"),
                  fileKey=safe_filekey, routeId=safe_text, exchangeId=safe_text, instanceUuid=safe_text)
INSTANCE = dict(IDENTITIES, instanceStatus=instance_status, invokeProviderStatus=instance_status,
                reqApplicationCode=safe_text, resApplicationCode=safe_text, errorCode=error_code, itemErrorCode=error_code,
                **{key: time_value for key in ("invokeStartTime", "invokeEndTime", "invokeProviderStartTime", "invokeProviderEndTime", "createTime", "itemCreateTime", "reqBodyCreateTime", "resBodyCreateTime")})


def event(raw, converters, pointer, code, summary, tz=None, observed=None):
    fields, suppressed = project(raw, converters)
    observed = observed or fields.get("invokeStartTime") or fields.get("startTime") or fields.get("createTime")
    stamp, normalized = timestamp(observed, tz)
    return dict(timestamp=stamp, normalizedTime=normalized, level=None, logger=None,
                **{key: fields.get(key) for key in IDENTITIES},
                locator=dict(kind="json", pointer=pointer),
                signal=dict(eventCode=code, category="observation", summary=summary, fields=fields),
                suppressed=suppressed, incomplete=False, repeatCount=1)


def collection_metadata(raw, kind):
    require(isinstance(raw, dict))
    out, suppressed = project(raw, dict(targetAlias=lambda v: safe_text(v, "alias"),
        commandKind=enum(*ENDPOINTS), startedAt=time_value, completedAt=time_value, exitCode=integer))
    if raw.get("commandKind") not in (None, kind):
        raise EvidenceError("METADATA_KIND_MISMATCH", "input")
    if "filters" in raw:
        require(isinstance(raw["filters"], dict))
        out["filters"], omitted = project(raw["filters"], dict(serviceName=IDENTITIES["serviceName"], serviceVersion=IDENTITIES["serviceVersion"],
            sessionId=safe_text, instanceUuid=safe_text, startTime=time_value, endTime=time_value, pageNum=integer, pageSize=integer))
        suppressed |= omitted
    out.update(origin="caller-supplied", suppressed=suppressed)
    return out


def safe_ids(values, converter=safe_text):
    require(isinstance(values, list))
    return [clean for value in values if (clean := converter(value)) is not None]


def adapt(document, kind, budget, tz=None):
    """Return safe source metadata, stop reasons and a lazy event stream."""
    meta = dict(endpointTemplate=ENDPOINTS[kind])
    warnings = []
    if "schemaVersion" in document:
        require(type(document["schemaVersion"]) is int and document["schemaVersion"] == 1)
    if "success" in document:
        require(type(document["success"]) is bool)
        if not document["success"]:
            raw_error = document.get("error")
            require(isinstance(raw_error, dict))
            converters = dict(code=error_code, category=error_code,
                httpStatus=lambda v: v if type(v) is int and 100 <= v <= 599 else None)
            failure = event(raw_error, converters, "/error", "CLI_COLLECTION_FAILED", "远程采集失败", tz)
            fields = failure["signal"]["fields"]
            fields["exitCode"] = integer(document.get("exitCode"))
            fields["requestId"] = safe_text(document.get("requestId"))
            fields.setdefault("httpStatus", None)
            failure["suppressed"] = True
            meta["collectionFailed"] = True
            return meta, warnings, iter([failure])
        require(isinstance(document.get("data"), dict))
        raw, prefix = document["data"], "/data"
    else:
        raw, prefix = document, ""
    if "schemaVersion" in raw:
        require(type(raw["schemaVersion"]) is int and raw["schemaVersion"] == 1)
    if kind == "instance-list":
        require(isinstance(raw.get("records"), list) and integer(raw.get("total")) is not None
                and integer(raw.get("pageNum")) not in (None, 0) and integer(raw.get("pageSize")) not in (None, 0))
        require(all(isinstance(row, dict) and isinstance(row.get("instanceUuid"), str) for row in raw["records"]))
        meta["pagination"] = {k: raw[k] for k in ("total", "pageNum", "pageSize")}
        meta["pagination"]["returned"] = len(raw["records"])
        meta["serverTimestamp"] = integer(raw.get("timestamp"))
        if raw["pageNum"] > 1 or raw["total"] > len(raw["records"]):
            warnings.append("PAGINATED_SCOPE")
        return meta, warnings, (event(row, INSTANCE, f"{prefix}/records/{i}", "INSTANCE_ROW", "实例及提供方记录", tz) for i, row in enumerate(raw["records"]))
    if kind == "instance-detail":
        require(isinstance(raw.get("instanceUuid"), str) and isinstance(raw.get("itemRecords"), list))
        require(all(isinstance(row, dict) for row in raw["itemRecords"]))
        meta["serverTimestamp"] = integer(raw.get("timestamp"))
        def details():
            main = event(raw, INSTANCE, prefix, "INSTANCE_DETAIL", "实例详情元数据", tz)
            main["signal"]["fields"].update(reqBodyPresent=raw.get("reqBody") is not None,
                resBodyPresent=raw.get("resBody") is not None, itemRecordCount=len(raw["itemRecords"]))
            yield main
            for i, row in enumerate(raw["itemRecords"]):
                item = event(row, INSTANCE, f"{prefix}/itemRecords/{i}", "INSTANCE_ITEM", "实例提供方明细", tz, row.get("invokeProviderStartTime") or row.get("itemCreateTime"))
                # Parent identity is explicit context; the locator still points
                # to the item. Keep this relationship separate from row fields.
                item["parentInstanceUuid"] = safe_text(raw["instanceUuid"])
                yield item
        return meta, warnings, details()
    if kind.startswith("diagnostics-"):
        require(isinstance(raw.get("runtime"), dict) and isinstance(raw.get("components"), list) and isinstance(raw.get("warnings"), list))
        require(all(isinstance(row, dict) and isinstance(row.get("component"), str) and isinstance(row.get("status"), str)
                    and isinstance(row.get("summary"), dict) for row in raw["components"]))
        meta["serverGeneratedAt"] = time_value(raw["runtime"].get("generatedAt"))
        meta["warningCount"] = len(raw["warnings"])
        if isinstance(raw.get("filters"), dict):
            meta["serverFilters"], _ = project(raw["filters"], dict(serviceName=IDENTITIES["serviceName"], serviceVersion=IDENTITIES["serviceVersion"], component=safe_text))
        def components():
            if raw["warnings"]:
                yield event({}, {}, prefix+"/warnings", "DIAGNOSTIC_WARNINGS", "存在未展开告警", tz, meta["serverGeneratedAt"]) | {"suppressed": True}
            for i, row in enumerate(raw["components"]):
                item = event(row, dict(component=safe_text, status=enum("OK", "WARN", "ERROR", "UNAVAILABLE", "UNKNOWN")),
                    f"{prefix}/components/{i}", "DIAGNOSTIC_COMPONENT", "组件当前诊断状态", tz, meta["serverGeneratedAt"])
                summary = row["summary"]
                clean, _ = project(summary, dict(reject=integer, pocH2FallbackEnabled=boolean))
                for group, keys in (("queue", ("size", "remainingCapacity", "activeThreads", "peakSize")),
                                    ("batch", ("processedTasks", "processedBatches", "taskLatencyP99Ms", "batchLatencyP99Ms"))):
                    if isinstance(summary.get(group), dict):
                        clean[group], _ = project(summary[group], {k: metric for k in keys})
                for key in ("storage", "instanceLogStorage", "instanceLogQueryStorage", "jsonKeywordQueryStorage"):
                    if key in summary:
                        mappings = {"mysql": "MYSQL", "h2": "H2"} if key == "storage" else {"mysql": "MYSQL", "h2-fallback": "H2_FALLBACK"}
                        value = summary[key]
                        clean[key] = None if value is None else mappings.get(value, "UNKNOWN") if isinstance(value, str) else "UNKNOWN"
                item["signal"]["fields"]["summary"] = clean
                item["suppressed"] = True
                yield item
        return meta, warnings, components()
    if kind == "route-status":
        require(integer(raw.get("totalFiles")) is not None and isinstance(raw.get("fileKeys"), list) and isinstance(raw.get("routeCounts"), dict))
        require(all(isinstance(ids, list) for ids in raw["routeCounts"].values()))
        item = event(raw, {k: integer for k in ("totalFiles", "totalRoutes", "totalCamelContexts", "activeCamelContexts")} | dict(dynamicLoaderActive=boolean), prefix, "ROUTE_STATUS", "当前路由装载状态", tz)
        fields = item["signal"]["fields"]
        fields["fileKeys"] = safe_ids(raw["fileKeys"], safe_filekey)
        fields["routeCounts"] = {key: safe_ids(ids) for key, ids in raw["routeCounts"].items() if safe_filekey(key)}
        return meta, warnings, iter([item])
    if kind == "route-detail":
        require(isinstance(raw.get("fileKey"), str) and isinstance(raw.get("routes"), list) and integer(raw.get("routeCount")) is not None)
        item = event(raw, dict(fileKey=safe_filekey, routeCount=integer,
            runtimeState=enum("STOPPED", "STARTING", "RUNNING", "FAILED", "UNKNOWN"), contextStatus=enum("NOT_FOUND", "STARTED", "STOPPED"),
            lastModified=integer, sourceLastModified=integer), prefix, "ROUTE_DETAIL", "当前路由文件状态", tz)
        item["signal"]["fields"]["routeIds"] = safe_ids(raw["routes"])
        return meta, warnings, iter([item])
    if kind == "deploy-status":
        require(isinstance(raw.get("deploymentId"), str) and isinstance(raw.get("status"), str))
        item = event(raw, dict(IDENTITIES, deploymentId=safe_text, status=enum(*DEPLOY_STATES),
            progress=lambda v: v if metric(v) is not None and v <= 100 else None,
            startTime=time_value, endTime=time_value, elapsedTime=integer, backupAvailable=boolean,
            fileCount=integer, routeCount=integer, operationType=enum("DEPLOY_PACKAGE", "DEPLOY", "ROLLBACK", "AI_ROUTE_SAVE", "SAVE_AI_ROUTE", "APPLY_AI_ROUTE"), sourceDeploymentId=safe_text),
            prefix, "DEPLOYMENT_STATUS", "部署状态记录", tz)
        if "routeIds" in raw:
            item["signal"]["fields"]["routeIds"] = safe_ids(raw["routeIds"])
        return meta, warnings, iter([item])
    require(kind == "log-snapshot")
    require(isinstance(raw.get("serviceName"), str) and isinstance(raw.get("serviceVersion"), str)
            and raw.get("window") == "RECENT_TAIL" and isinstance(raw.get("files"), list))
    require(all(isinstance(row, dict) and isinstance(row.get("file"), str) and isinstance(row.get("lines"), list)
                and all(isinstance(line, str) for line in row["lines"]) for row in raw["files"]))
    meta.update(serverGeneratedAt=time_value(raw.get("queriedAt")), window="RECENT_TAIL",
                serviceName=safe_text(raw["serviceName"], "service"), serviceVersion=safe_text(raw["serviceVersion"], "version"),
                logsExist=boolean(raw.get("logsExist")), filesTruncated=boolean(raw.get("filesTruncated")), remoteFiles=[])
    if raw.get("filesTruncated") is True:
        warnings.append("REMOTE_FILE_LIMIT")
    for i, row in enumerate(raw["files"]):
        clean, omitted = project(row, dict(file=safe_path, bytesRead=integer, truncated=boolean, changedDuringRead=boolean, readError=error_code))
        clean.update(pointer=f"{prefix}/files/{i}", suppressed=omitted)
        meta["remoteFiles"].append(clean)
        if row.get("truncated") is True or row.get("changedDuringRead") is True or row.get("readError"):
            warnings.append("REMOTE_SOURCE_INCOMPLETE")
    def snapshot_lines():
        for i, row in enumerate(raw["files"]):
            if row.get("changedDuringRead") is True or row.get("readError"):
                continue
            for j, line in enumerate(row["lines"]):
                budget.check()
                pointer = f"{prefix}/files/{i}/lines/{j}"
                data = (line+"\n").encode("utf-8")
                if len(data) > budget.limits["record_bytes"]:
                    item = event({}, {}, pointer, "UNCLASSIFIED", "记录超限，正文已抑制", tz) | {"suppressed": True, "incomplete": True, "_layoutParsed": False}
                else:
                    parsed, reason = parse_record(data, 0, len(data), "byte", tz, raw["serviceName"], raw["serviceVersion"])
                    if reason:
                        item = event({}, {}, pointer, "UNCLASSIFIED", "未知布局，正文已抑制", tz)
                        item["suppressed"] = True
                        item["_layoutParsed"] = False
                    else:
                        item, _ = parsed
                item["locator"] = dict(kind="json", pointer=pointer)
                if safe_path(row["file"]):
                    item["locator"]["serverFile"] = row["file"]
                item["repeatCount"] = 1
                yield item
    return meta, warnings, snapshot_lines()
