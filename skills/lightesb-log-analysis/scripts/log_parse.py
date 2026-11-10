"""Known layouts and allowlisted runtime signals. Unknown messages stay private."""
from __future__ import annotations

from datetime import datetime, timezone
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from log_io import EvidenceError

SENSITIVE = re.compile(r"password|secret|token|authorization|SYNTHETIC_", re.I)
HEADER = re.compile(rb"^\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d\.\d{3} \|")
STAMP = re.compile(r"^\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d\.\d{3}$")
IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}")
SERVICE = re.compile(r"[A-Za-z0-9_-]{1,100}")
VERSION = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")
APP_PATTERN = "%d{yyyy-MM-dd HH:mm:ss.SSS} | %-5.5p | %c{1} | %m%n"
SERVICE_PATTERN = "%d{yyyy-MM-dd HH:mm:ss.SSS} | %-5.5p | [%X{service.name}-%X{service.version}] | %X{route.id} | %X{exchange.id} | %-30.30c{1} | %m%n"
CONSTANTS = {"LOG_DIR", "LOG_PATTERN", "LOG_CHARSET"}


def safe_text(value, kind="id"):
    if not isinstance(value, str) or SENSITIVE.search(value):
        return None
    rule = {"service": SERVICE, "version": VERSION, "logger": re.compile(r"[A-Za-z0-9_.$-]{1,64}"),
            "alias": re.compile(r"[A-Za-z0-9_-]{1,48}")}.get(kind, IDENTIFIER)
    if kind == "version" and len(value) > 32:
        return None
    return value if rule.fullmatch(value) else None


def safe_filekey(value):
    if not isinstance(value, str) or len(value) > 256 or SENSITIVE.search(value):
        return None
    parts = value.split("@")
    if len(parts) < 3 or not safe_text(parts[0], "service") or not safe_text(parts[1], "version"):
        return None
    if any(p in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", p) for p in parts[2:]):
        return None
    return value if parts[-1].endswith(".xml") else None


def safe_path(value):
    if not isinstance(value, str) or len(value) > 512 or SENSITIVE.search(value):
        return None
    return value if all(p not in ("", ".", "..") and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", p) for p in value.split("/")) else None


def number(value):
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return parsed if 0 <= parsed <= 2**53-1 else None


def timestamp(value, tz=None):
    if not isinstance(value, str) or len(value) > 40:
        return None, None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None and tz:
            zone = ZoneInfo(tz)
            if dt.replace(tzinfo=zone, fold=0).utcoffset() != dt.replace(tzinfo=zone, fold=1).utcoffset():
                return value, None
            dt = dt.replace(tzinfo=zone)
        normalized = dt.astimezone(timezone.utc).isoformat() if dt.tzinfo else None
        return value, normalized
    except (ValueError, ZoneInfoNotFoundError):
        return None, None


def layout_config(data):
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeError:
        return {}, ["CONFIG_ENCODING"]
    props, duplicates = {}, set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or line.endswith("\\"):
            return {}, ["CONFIG_SYNTAX_UNSUPPORTED"]
        allowed = key in {"property." + k for k in CONSTANTS} or re.fullmatch(r"(?:appender\.[A-Za-z0-9_-]+\.(?:name|fileName|filePattern|layout\.pattern|layout\.charset)|(?:rootLogger|logger\.[A-Za-z0-9_-]+)\.(?:name|appenderRef\.[A-Za-z0-9_-]+\.ref))", key)
        if not allowed:
            continue
        if key in props:
            duplicates.add(key)
        props[key] = value
    if duplicates:
        return {}, ["CONFIG_DUPLICATE_KEY"]
    warnings = set()

    def expand(value, stack=(), depth=0, count=None):
        count = [0] if count is None else count
        if depth > 4 or len(value.encode()) > 8192:
            raise EvidenceError("REFERENCE_LIMIT", "layout")
        def replace(match):
            name = match.group(1)
            count[0] += 1
            if count[0] > 32:
                raise EvidenceError("REFERENCE_LIMIT", "layout")
            if name not in CONSTANTS:
                raise EvidenceError("UNSUPPORTED_REFERENCE", "layout")
            if name in stack:
                raise EvidenceError("REFERENCE_CYCLE", "layout")
            if "property." + name not in props:
                raise EvidenceError("REFERENCE_MISSING", "layout")
            return expand(props["property." + name], stack+(name,), depth+1, count)
        result = re.sub(r"\$\{([^{}]*)\}", replace, value)
        if "${" in result or "$${" in value or len(result.encode()) > 8192:
            raise EvidenceError("UNSUPPORTED_REFERENCE", "layout")
        return result

    appenders = {}
    for key, value in props.items():
        if not key.startswith("appender."):
            continue
        _, name, field = key.split(".", 2)
        try:
            val = expand(value)
        except EvidenceError as exc:
            warnings.add(exc.code)
            continue
        app = appenders.setdefault(name, {})
        if field in ("fileName", "filePattern"):
            # Values are used only for matching an explicitly selected source,
            # never as a new read authorization; raw paths are not emitted.
            app[field] = val
        elif field == "layout.pattern":
            app["layout"] = "service" if val == SERVICE_PATTERN else "application" if val == APP_PATTERN else "unknown"
        elif field == "layout.charset":
            app["charset"] = "UTF-8" if val.upper() == "UTF-8" else "unsupported"
        elif field == "name":
            app["name"] = safe_text(val)
    referenced = set()
    for key, value in props.items():
        if key.startswith(("rootLogger.", "logger.")) and ".appenderRef." in key and key.endswith(".ref"):
            owner = key.split(".appenderRef.", 1)[0]
            try:
                if owner != "rootLogger" and not safe_text(expand(props.get(owner + ".name", "")), "logger"):
                    warnings.add("LOGGER_REFERENCE_UNRESOLVED")
                    continue
                referenced.add(expand(value))
            except EvidenceError as exc:
                warnings.add(exc.code)
    names = [app.get("name") for app in appenders.values()]
    for app in appenders.values():
        app["referenced"] = app.get("name") is not None and app.get("name") in referenced and names.count(app["name"]) == 1
        if app.get("name") and names.count(app["name"]) > 1:
            warnings.add("APPENDER_NAME_CONFLICT")
    return appenders, sorted(warnings)


def signal(logger, message):
    if logger == "EnhancedRouteLoader":
        specs = [
            (r"服务配置中server.running=false，跳过路由加载: (.+)", "ROUTE_DISABLED", "configuration", "配置禁用，跳过路由加载", ("fileKey",)),
            (r"AI路由未启用，跳过加载: (.+)", "AI_ROUTE_DISABLED", "configuration", "AI路由未启用", ("fileKey",)),
            (r"路由/配置未发生变化（锁内二次检查），跳过加载: (.+)", "ROUTE_UNCHANGED", "lifecycle", "配置未变化，跳过加载", ("fileKey",)),
            (r"服务配置加载成功: 服务名=(.+), 版本=(.+), 配置项数量=(\d+)", "SERVICE_CONFIG_LOADED", "configuration", "服务配置加载完成", ("serviceName", "serviceVersion", "propertyCount")),
            (r"成功加载路由文件: (.+) 到CamelContext, 包含 (\d+) 个路由: \[(.*)\]", "ROUTE_LOADED", "lifecycle", "路由文件加载完成", ("fileKey", "routeCount", "routeIds")),
            (r"可选扩展组件注册失败，继续加载: (.*)", "OPTIONAL_CAPABILITY_FAILED", "warning", "可选扩展组件失败后继续加载", ("_private",)),
            (r"可选异常处理能力注册失败，继续加载: (.*)", "OPTIONAL_CAPABILITY_FAILED", "warning", "可选异常处理能力失败后继续加载", ("_private",)),
            (r"服务 (.+) 的日志系统配置完成", "SERVICE_LOG_CONFIGURED", "configuration", "服务日志配置完成", ("fileKey",)),
        ]
    elif logger == "EnhancedDynamicRouteLoader":
        specs = [
            (r"正常模式：全量加载路由目录 (.+)", "ROUTE_DIRECTORY_MODE", "configuration", "全量目录模式", ("_private",)),
            (r"临时测试模式启用：仅加载服务目录 (.+)", "ROUTE_DIRECTORY_MODE", "configuration", "指定目录模式", ("_private",)),
            (r"增强动态路由加载器启动阶段耗时 - 配置初始化: (\d+)ms, 路由目录解析: (\d+)ms, 初始路由加载: (\d+)ms, 状态同步: (\d+)ms, 文件监听启动: (\d+)ms, 总计: (\d+)ms", "STARTUP_STAGE_TIMING", "performance", "启动阶段耗时", ("configurationMs", "directoryMs", "initialLoadMs", "statusSyncMs", "watcherMs", "totalMs")),
            (r"初始路由加载完成 - 成功: (\d+), 失败: (\d+), 总计: (\d+)", "INITIAL_LOAD_SUMMARY", "lifecycle", "初始加载结果统计", ("successCount", "failureCount", "totalCount")),
            (r"初始路由加载汇总 - 已加载CamelContext: (\d+), 总路由数: (\d+)", "INITIAL_LOAD_SUMMARY", "lifecycle", "初始上下文及路由统计", ("contextCount", "routeCount")),
            (r"文件监控器已启动，监控目录数量: (\d+)", "WATCHER_STARTED", "lifecycle", "文件监控器已启动", ("directoryCount",)),
            (r"忽略重复的文件事件: (.+) \(防抖\)", "FILE_EVENT_DEBOUNCED", "lifecycle", "重复文件事件被防抖跳过", ("_private",)),
        ]
    else:
        specs = []
    for pattern, code, category, summary, names in specs:
        match = re.fullmatch(pattern, message)
        if not match:
            continue
        fields, suppressed = {}, False
        for key, value in zip(names, match.groups()):
            if key == "_private":
                suppressed = True
                continue
            if key == "fileKey":
                clean = safe_filekey(value)
            elif key == "serviceName":
                clean = safe_text(value, "service")
            elif key == "serviceVersion":
                clean = safe_text(value, "version")
            elif key == "routeIds":
                items = [] if not value else value.split(", ")
                clean = [safe_text(x) for x in items[:100]]
                suppressed |= len(items) > 100 or any(x is None for x in clean)
                clean = [x for x in clean if x is not None]
            else:
                clean = number(value)
            suppressed |= clean is None
            if clean is not None:
                fields[key] = clean
        if code == "OPTIONAL_CAPABILITY_FAILED":
            fields.update(continued=True, capability="exception" if pattern.startswith("可选异常处理") else "extension")
        if code == "ROUTE_DIRECTORY_MODE":
            fields["mode"] = "full" if message.startswith("正常") else "selected"
        if code == "STARTUP_STAGE_TIMING":
            fields["sampleCount"] = 1
        return dict(eventCode=code, category=category, summary=summary, fields=fields), suppressed
    return dict(eventCode="UNCLASSIFIED", category="unknown", summary="未识别消息，正文已抑制", fields={}), True


def parse_record(data, start, end, unit, tz=None, service=None, version=None):
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeError:
        return None, "UTF8_INCOMPLETE"
    lines = text.splitlines()
    if not lines:
        return None, "EMPTY_RECORD"
    first = lines[0]
    pieces = first.split(" | ", 3)
    if len(pieces) != 4 or not STAMP.fullmatch(pieces[0]):
        return None, "UNKNOWN_LAYOUT"
    raw_time, normalized = timestamp(pieces[0], tz)
    if raw_time is None:
        return None, "INVALID_TIMESTAMP"
    level = pieces[1].strip()
    if level not in ("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL", "OFF", "ALL"):
        return None, "UNKNOWN_LEVEL"
    service_name = service_version = route = exchange = None
    structure_suppressed = False
    if pieces[2].startswith("["):
        pieces = first.split(" | ", 6)
        if len(pieces) != 7 or not pieces[2].endswith("]"):
            return None, "UNKNOWN_LAYOUT"
        combined = pieces[2][1:-1]
        if service and version and combined == service + "-" + version:
            service_name, service_version = safe_text(service, "service"), safe_text(version, "version")
        else:
            split = re.fullmatch(r"([A-Za-z0-9_-]+)-(v[0-9]+\.[0-9]+\.[0-9]+)", combined)
            if split:
                service_name, service_version = safe_text(split[1], "service"), safe_text(split[2], "version")
        route, exchange = safe_text(pieces[3].strip()), safe_text(pieces[4].strip())
        logger, message, layout = safe_text(pieces[5].strip(), "logger"), pieces[6], "service"
        structure_suppressed = bool(combined and combined != "-" and (service_name is None or service_version is None))
        structure_suppressed |= bool(pieces[3].strip() and route is None) or bool(pieces[4].strip() and exchange is None)
        structure_suppressed |= bool(pieces[5].strip() and logger is None)
    else:
        logger, message, layout = safe_text(pieces[2].strip(), "logger"), pieces[3], "application"
        structure_suppressed = bool(pieces[2].strip() and logger is None)
    sig, suppressed = signal(logger, message)
    if service_name is None:
        service_name = sig["fields"].get("serviceName")
        service_version = sig["fields"].get("serviceVersion")
        if sig["fields"].get("fileKey"):
            service_name, service_version = sig["fields"]["fileKey"].split("@")[:2]
    # Continuations can contain payload/exception secrets. Never emit them.
    suppressed |= len(lines) > 1 or structure_suppressed
    event = dict(timestamp=raw_time, normalizedTime=normalized, level=level, logger=logger,
                 serviceName=service_name, serviceVersion=service_version,
                 fileKey=sig["fields"].get("fileKey"), routeId=route, exchangeId=exchange,
                 instanceUuid=None, locator=dict(kind="file", start=start, end=end, unit=unit),
                 signal=sig, suppressed=suppressed, incomplete=False)
    return (event, layout), None


def records(data, start, limit):
    """Yield bounded complete record spans; never treat tail fragments as headers."""
    pending, offset, record_start, dropped, pending_size = [], start, start, False, 0
    for line in data.splitlines(keepends=True):
        if HEADER.match(line):
            if pending:
                yield b"".join(pending), record_start, offset, "RECORD_LIMIT" if dropped else None
            pending, record_start, dropped, pending_size = [], offset, False, 0
        elif not pending and not dropped:
            yield b"", offset, offset+len(line), "ORPHAN_FRAGMENT"
            offset += len(line)
            continue
        if not dropped:
            if pending_size + len(line) > limit:
                dropped = True
                pending = [b""]
            else:
                pending.append(line)
                pending_size += len(line)
        offset += len(line)
    if pending:
        reason = "RECORD_LIMIT" if dropped else "INCOMPLETE_LAST_RECORD" if not data.endswith(b"\n") else None
        yield b"".join(pending), record_start, offset, reason
