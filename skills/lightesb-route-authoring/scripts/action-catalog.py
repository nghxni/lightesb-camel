#!/usr/bin/env python3
"""Build a deterministic LightESB Action catalog from service directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qsl, urlsplit


CATALOG_SCHEMA_VERSION = "lightesb.action-catalog/v1alpha1"
DECLARATION_SCHEMA_VERSION = "1"
MAX_PROPERTIES_BYTES = 512 * 1024
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_SCHEMA_BYTES = 2 * 1024 * 1024
MAX_SERVICES = 2_000
MAX_ACTIONS_PER_SERVICE = 100
MAX_ACTIONS = 10_000
MAX_ROOT_ENTRIES = 5_000
MAX_SERVICE_ENTRIES = 256

ACTION_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
SCOPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._/-]{0,127}$")
PLACEHOLDER_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
MEDIA_TYPE_RE = re.compile(r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(?:password|passwd|secret|token|api[-_.]?key|cookie|authorization)\s*[:=]\s*\S+"
)
ABSOLUTE_PATH_RE = re.compile(r"(?:^|\s)(?:/(?:home|Users|tmp|var|etc)/|[A-Za-z]:[\\/])")
SECRET_QUERY_PARTS = ("password", "passwd", "secret", "token", "apikey", "cookie", "authorization", "username")
TARGET_QUERY_KEYS = {"user", "brokerurl", "endpoint", "node", "clientid", "host", "address", "uri"}

ACTION_FIELDS = {
    "route-id",
    "name",
    "description",
    "interaction-pattern",
    "agent-callable",
    "side-effect",
    "idempotency",
    "retry-policy",
    "approval-required",
    "exposure",
    "required-config-keys",
    "credential-aliases",
    "required-scopes",
}
LIST_FIELDS = {"required-config-keys", "credential-aliases", "required-scopes"}
ROUTE_METADATA_KEYS = {
    "lightesb.action.input.schema",
    "lightesb.action.input.media-type",
    "lightesb.action.input.contract-stage",
    "lightesb.action.input.contract-processor-ref",
    "lightesb.action.output.schema",
    "lightesb.action.output.media-type",
    "lightesb.action.error.schema",
    "lightesb.action.error.media-type",
}


class CatalogError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PropertiesFile:
    values: dict[str, str]
    action_keys: set[str]


def fail(code: str, message: str) -> None:
    raise CatalogError(code, message)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def reject_symlink(path: Path, code: str = "ACTION_SOURCE_UNSAFE") -> None:
    if path.is_symlink():
        fail(code, f"拒绝 symlink：{path.name}")


def read_limited(path: Path, limit: int, kind: str) -> str:
    reject_symlink(path)
    if not path.is_file():
        fail("ACTION_SOURCE_UNSAFE", f"缺少 {kind}：{path.name}")
    size = path.stat().st_size
    if size > limit:
        fail("ACTION_LIMIT_EXCEEDED", f"{kind} 超过 {limit} bytes：{path.name}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail("ACTION_SOURCE_UNSAFE", f"{kind} 不是 UTF-8：{path.name}")
    raise AssertionError("unreachable")


def limited_children(path: Path, limit: int) -> list[Path]:
    children: list[Path] = []
    with os.scandir(path) as entries:
        for entry in entries:
            children.append(Path(entry.path))
            if len(children) > limit:
                fail("ACTION_LIMIT_EXCEEDED", f"目录条目超过 {limit}：{path.name}")
    return sorted(children, key=lambda child: child.name)


def parse_properties(path: Path, *, allow_action: bool) -> PropertiesFile:
    text = read_limited(path, MAX_PROPERTIES_BYTES, "properties")
    values: dict[str, str] = {}
    action_keys: set[str] = set()
    logical_lines: list[tuple[int, str]] = []
    pending = ""
    pending_number = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        if pending:
            pending += raw.lstrip()
        else:
            pending = raw
            pending_number = number
        continuation = (len(pending) - len(pending.rstrip("\\"))) % 2 == 1
        if continuation:
            key = pending.split("=", 1)[0].split(":", 1)[0].strip()
            if key.startswith("action.") or key.startswith("actions."):
                fail("ACTION_DECLARATION_DUPLICATE", f"{path.name}:{pending_number} 禁止 Action 续行")
            pending = pending[:-1]
            continue
        logical_lines.append((pending_number, pending))
        pending = ""
    if pending:
        fail("ACTION_SOURCE_UNSAFE", f"{path.name}:{pending_number} properties 续行未闭合")

    for number, raw in logical_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", "!")):
            continue
        match = re.fullmatch(r"([^=:\s]+)\s*(=|:)\s*(.*)", stripped)
        if not match:
            fail("ACTION_SOURCE_UNSAFE", f"{path.name}:{number} 不是 key=value")
        key, separator, value = match.group(1), match.group(2), match.group(3).strip()
        is_action = key.startswith("action.") or key.startswith("actions.")
        if is_action:
            if not allow_action:
                fail("ACTION_FIELD_UNKNOWN", f"Action 声明只能位于 service.config.properties：{key}")
            if separator != "=" or "\\" in key:
                fail("ACTION_DECLARATION_DUPLICATE", f"Action key 必须使用未转义 key=value：{key}")
            if key in action_keys:
                fail("ACTION_DECLARATION_DUPLICATE", f"Action key 重复：{key}")
            action_keys.add(key)
        values[key] = value
    return PropertiesFile(values, action_keys)


def parse_list(value: str, field: str, pattern: re.Pattern[str]) -> list[str]:
    if value == "":
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in value.split(","):
        item = raw.strip()
        if not item or not pattern.fullmatch(item) or "=" in item:
            fail("ACTION_FIELD_UNKNOWN", f"列表字段格式非法：{field}")
        if item in seen:
            fail("ACTION_DECLARATION_DUPLICATE", f"列表字段存在重复值：{field}")
        seen.add(item)
        result.append(item)
    return sorted(result)


def parse_action_ids(value: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in value.split(","):
        action_id = raw.strip()
        if not action_id or len(action_id) > 64 or not ACTION_ID_RE.fullmatch(action_id):
            fail("ACTION_ID_INVALID", f"actionId 非法：{action_id or '-'}")
        if action_id in seen:
            fail("ACTION_DECLARATION_DUPLICATE", f"actionId 重复：{action_id}")
        seen.add(action_id)
        result.append(action_id)
    return sorted(result)


def parse_bool(value: str, field: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    fail("ACTION_BOOLEAN_INVALID", f"布尔字段必须为 true/false：{field}")
    raise AssertionError("unreachable")


def require_scalar(fields: dict[str, str], field: str) -> str:
    value = fields.get(field)
    if value is None or value == "":
        fail("ACTION_FIELD_MISSING", f"缺少必填字段：{field}")
    if any(ord(char) < 32 for char in value):
        fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", f"字段含控制字符：{field}")
    return value


def reject_sensitive_text(value: str, field: str) -> None:
    if (
        SECRET_ASSIGNMENT_RE.search(value)
        or ABSOLUTE_PATH_RE.search(value)
        or re.search(r"(?i)://[^/?#\s]*@", value)
    ):
        fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", f"字段疑似包含敏感实值：{field}")


def parse_action_fields(action_id: str, service_properties: PropertiesFile) -> dict[str, str]:
    prefix = f"action.{action_id}."
    fields: dict[str, str] = {}
    for key in service_properties.action_keys:
        if not key.startswith(prefix):
            continue
        field = key[len(prefix):]
        if field not in ACTION_FIELDS:
            fail("ACTION_FIELD_UNKNOWN", f"未知 Action 字段：{field}")
        fields[field] = service_properties.values[key]
    for key in service_properties.action_keys:
        if key.startswith("action.") and not any(
            key.startswith(f"action.{declared}.")
            for declared in (item.strip() for item in service_properties.values.get("actions.ids", "").split(","))
        ):
            fail("ACTION_FIELD_UNKNOWN", f"存在未列入 actions.ids 的声明：{key}")
    return fields


def safe_schema_path(service_dir: Path, raw: str) -> Path:
    if not raw or "\\" in raw:
        fail("ACTION_SCHEMA_PATH_INVALID", "schema 路径为空或含反斜杠")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or relative.as_posix() != raw or ".." in relative.parts or "." in relative.parts:
        fail("ACTION_SCHEMA_PATH_INVALID", f"schema 路径越界：{raw}")
    candidate = service_dir.joinpath(*relative.parts)
    current = service_dir
    for part in relative.parts:
        current = current / part
        reject_symlink(current, "ACTION_SCHEMA_PATH_INVALID")
    if not candidate.is_file():
        fail("ACTION_SCHEMA_MISSING", f"schema 不存在：{raw}")
    if not is_within(candidate.resolve(), service_dir.resolve()):
        fail("ACTION_SCHEMA_PATH_INVALID", f"schema 路径越界：{raw}")
    return candidate


def schema_descriptor(service_dir: Path, metadata: dict[str, str], direction: str) -> dict[str, Any] | None:
    schema_key = f"lightesb.action.{direction}.schema"
    media_key = f"lightesb.action.{direction}.media-type"
    raw_path = metadata.get(schema_key)
    media_type = metadata.get(media_key)
    if bool(raw_path) != bool(media_type):
        fail("ACTION_SCHEMA_MEDIA_TYPE_MISSING", f"{direction} schema 与 media type 必须成对声明")
    if not raw_path:
        return None
    if len(media_type) > 128 or not MEDIA_TYPE_RE.fullmatch(media_type):
        fail("ACTION_SCHEMA_INVALID", f"media type 非法：{direction}")
    schema_path = safe_schema_path(service_dir, raw_path)
    content = read_limited(schema_path, MAX_SCHEMA_BYTES, "schema")
    if media_type == "application/schema+json":
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            fail("ACTION_SCHEMA_INVALID", f"JSON Schema 无法解析：{raw_path}")
        if not isinstance(parsed, dict):
            fail("ACTION_SCHEMA_INVALID", f"JSON Schema 顶层必须为 object：{raw_path}")
    descriptor: dict[str, Any] = {
        "mediaType": media_type,
        "schema": raw_path,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
    if direction == "input":
        descriptor["contractStage"] = metadata.get("lightesb.action.input.contract-stage")
        descriptor["processorRef"] = metadata.get("lightesb.action.input.contract-processor-ref")
    return descriptor


def route_metadata(route: ET.Element) -> dict[str, str]:
    metadata: dict[str, str] = {}
    seen_from = False
    for child in list(route):
        name = local_name(child.tag)
        if name == "from":
            seen_from = True
        if name != "routeProperty":
            continue
        key = (child.get("key") or "").strip()
        value = (child.get("value") or "").strip()
        if seen_from or key not in ROUTE_METADATA_KEYS or not value:
            fail("ACTION_ROUTE_METADATA_INVALID", f"routeProperty 非法或位置错误：{key or '-'}")
        if key in metadata:
            fail("ACTION_ROUTE_METADATA_INVALID", f"routeProperty 重复：{key}")
        metadata[key] = value
    return metadata


def route_from(route: ET.Element) -> ET.Element:
    entries = [child for child in list(route) if local_name(child.tag) == "from"]
    if len(entries) != 1 or not entries[0].get("uri"):
        fail("ACTION_INTERACTION_CONFLICT", "入口 route 必须恰有一个 from URI")
    return entries[0]


def endpoint_scheme(uri: str) -> str:
    match = re.match(r"([A-Za-z][A-Za-z0-9+.-]*):", uri)
    if not match:
        fail("ACTION_ENDPOINT_PROFILE_UNKNOWN", "入口 URI 缺少 component scheme")
    return match.group(1).lower()


def placeholder_only(value: str) -> bool:
    match = re.fullmatch(r"\{\{\s*([^{}]+?)\s*\}\}", value)
    return bool(match and NAME_RE.fullmatch(match.group(1)))


def client_id_template(value: str) -> bool:
    match = re.fullmatch(r"\{\{\s*([^{}]+?)\s*\}\}(?:[A-Za-z0-9._-]{0,64})", value)
    return bool(match and NAME_RE.fullmatch(match.group(1)))


def sensitive_query_key(key: str) -> bool:
    normalized = re.sub(r"[-_.]", "", key).lower()
    return any(part in normalized for part in SECRET_QUERY_PARTS) or normalized in TARGET_QUERY_KEYS


def safe_uri_template(uri: str, scheme: str) -> str:
    if any(ord(char) < 32 for char in uri) or re.search(r"(?i)://[^/?#\s]*@", uri):
        fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "入口 URI 含控制字符或 userinfo")
    for key in PLACEHOLDER_RE.findall(uri):
        if not NAME_RE.fullmatch(key):
            fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "入口 URI 占位符 key 非法")
    query = uri.split("?", 1)[1] if "?" in uri else ""
    for key, value in parse_qsl(query, keep_blank_values=True):
        placeholder_safe = client_id_template(value) if key.lower() == "clientid" else placeholder_only(value)
        if sensitive_query_key(key) and not placeholder_safe:
            fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", f"入口 URI 敏感参数必须使用占位符：{key}")
    if scheme in {"paho-mqtt5", "milo-client"} and not PLACEHOLDER_RE.search(uri):
        fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "工业/消息入口 URI 必须使用配置占位符")
    nested = uri.split(":", 1)[1] if scheme == "undertow" else uri
    if scheme in {"undertow", "http", "https"}:
        try:
            host = urlsplit(nested).hostname
        except ValueError:
            fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "HTTP URI authority 非法")
        if host and host not in {"0.0.0.0", "127.0.0.1", "localhost"} and not placeholder_only(host):
            fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "HTTP URI host 必须是绑定地址或配置占位符")
    return uri


def http_details(uri: str, scheme: str) -> tuple[list[str], str | None]:
    if scheme not in {"undertow", "platform-http"}:
        return [], None
    method_value = ""
    for key, value in parse_qsl(uri.split("?", 1)[1] if "?" in uri else "", keep_blank_values=True):
        if key.lower() == "httpmethodrestrict":
            method_value = value
    methods = sorted({item.strip().upper() for item in method_value.split(",") if item.strip()})
    nested = uri.split(":", 1)[1]
    path = urlsplit(nested).path or None
    return methods, path


def validate_endpoint_profile(route: ET.Element, scheme: str, interaction: str) -> None:
    if interaction == "requestReply" and scheme in {"undertow", "platform-http"}:
        return
    if interaction == "oneWayConsumer" and scheme in {"paho-mqtt5", "milo-client"}:
        return
    if interaction == "scheduled" and scheme in {"timer", "quartz", "scheduler"}:
        return
    if interaction == "oneWayProducer":
        operational = [
            child for child in list(route)
            if local_name(child.tag) not in {"routeProperty", "from"}
        ]
        first = operational[0] if operational else None
        in_only = bool(
            first is not None
            and local_name(first.tag) == "setExchangePattern"
            and ((first.get("pattern") or first.text or "").strip() == "InOnly")
        )
        if in_only:
            return
    fail("ACTION_ENDPOINT_PROFILE_UNKNOWN", f"入口 scheme 与交互模式无受支持 profile：{scheme}/{interaction}")


def processor_locations(route: ET.Element, processor_ref: str) -> tuple[int, int]:
    matches = 0
    safe_matches = 0

    def visit(element: ET.Element, in_error: bool) -> None:
        nonlocal matches, safe_matches
        name = local_name(element.tag)
        next_error = in_error or name in {"doCatch", "doFinally", "onException"}
        if name == "process" and (element.get("ref") or "").strip() == processor_ref:
            matches += 1
            if not next_error:
                safe_matches += 1
        for child in list(element):
            visit(child, next_error)

    visit(route, False)
    return matches, safe_matches


def validate_contract_stage(route: ET.Element, input_contract: dict[str, Any] | None) -> None:
    if input_contract is None:
        return
    stage = input_contract.get("contractStage")
    processor_ref = input_contract.get("processorRef")
    if stage == "entry" and not processor_ref:
        return
    if stage == "normalized" and processor_ref and NAME_RE.fullmatch(processor_ref):
        matches, safe_matches = processor_locations(route, processor_ref)
        if matches == 1 and safe_matches == 1:
            return
    fail("ACTION_CONTRACT_STAGE_INVALID", "contract stage 与 processor ref 不一致或无法唯一定位")


def validate_interaction_contracts(
    interaction: str,
    input_contract: dict[str, Any] | None,
    output_contract: dict[str, Any] | None,
) -> None:
    input_required = interaction in {"requestReply", "oneWayProducer", "oneWayConsumer"}
    output_required = interaction == "requestReply"
    if input_required and input_contract is None:
        fail("ACTION_SCHEMA_REQUIRED", f"{interaction} 必须声明 input schema")
    if not input_required and input_contract is not None:
        fail("ACTION_SCHEMA_FORBIDDEN", f"{interaction} 禁止 input schema")
    if output_required and output_contract is None:
        fail("ACTION_SCHEMA_REQUIRED", f"{interaction} 必须声明 output schema")
    if not output_required and output_contract is not None:
        fail("ACTION_SCHEMA_FORBIDDEN", f"{interaction} 禁止 output schema")


def outbound_steps(route: ET.Element) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for element in route.iter():
        if local_name(element.tag) not in {"to", "toD"}:
            continue
        uri = (element.get("uri") or "").strip()
        if not uri:
            continue
        dynamic_target = re.match(r"^\{\{\s*([^{}]+?)\s*\}\}(?:\?|$)", uri)
        if dynamic_target:
            if not NAME_RE.fullmatch(dynamic_target.group(1)):
                fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "动态出站目标占位符 key 非法")
            scheme = "dynamic"
            safe_uri_template(f"dynamic:{uri}", scheme)
        else:
            scheme = endpoint_scheme(uri)
            safe_uri_template(uri, scheme)
        config_keys = sorted(set(PLACEHOLDER_RE.findall(uri)))
        if any(not NAME_RE.fullmatch(key) for key in config_keys):
            fail("ACTION_SENSITIVE_VALUE_FORBIDDEN", "出站 URI 占位符 key 非法")
        steps.append({
            "component": scheme,
            "configKeys": config_keys,
        })
    return steps


def canonical_element(element: ET.Element) -> Any:
    text = (element.text or "").strip()
    return [
        local_name(element.tag),
        sorted((key, value) for key, value in element.attrib.items()),
        text or None,
        [canonical_element(child) for child in list(element)],
    ]


def source_digest(fields: dict[str, Any], route: ET.Element, contracts: list[dict[str, Any] | None]) -> str:
    material = {
        "declaration": fields,
        "route": canonical_element(route),
        "schemas": sorted(
            (contract["schema"], contract["sha256"])
            for contract in contracts
            if contract is not None
        ),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def analyze_action(
    service_dir: Path,
    route_file: Path,
    route: ET.Element,
    action_id: str,
    fields: dict[str, str],
    merged_config: dict[str, str],
) -> dict[str, Any]:
    route_id = require_scalar(fields, "route-id")
    name = require_scalar(fields, "name")
    description = require_scalar(fields, "description")
    if len(name) > 80 or len(description) > 500:
        fail("ACTION_FIELD_UNKNOWN", "name/description 超过长度限制")
    reject_sensitive_text(name, "name")
    reject_sensitive_text(description, "description")

    interaction = require_scalar(fields, "interaction-pattern")
    if interaction not in {"requestReply", "oneWayProducer", "oneWayConsumer", "scheduled"}:
        fail("ACTION_ENUM_INVALID", "interaction-pattern 非法")
    side_effect = require_scalar(fields, "side-effect")
    if side_effect not in {"read", "write", "destructive"}:
        fail("ACTION_ENUM_INVALID", "side-effect 非法")

    agent_callable = parse_bool(fields.get("agent-callable", "false"), "agent-callable")
    idempotency = fields.get("idempotency", "none")
    retry_policy = fields.get("retry-policy", "none")
    approval_required = parse_bool(fields.get("approval-required", "false"), "approval-required")
    if idempotency not in {"none", "supported", "required"} or retry_policy not in {"none", "safe", "idempotent"}:
        fail("ACTION_ENUM_INVALID", "idempotency/retry-policy 非法")
    if side_effect in {"write", "destructive"}:
        for required in ("idempotency", "retry-policy", "approval-required"):
            if required not in fields:
                fail("ACTION_FIELD_MISSING", f"{side_effect} 必须显式声明：{required}")
    if retry_policy == "safe" and side_effect != "read":
        fail("ACTION_SIDE_EFFECT_CONFLICT", "safe retry 只允许 read")
    if retry_policy == "idempotent" and idempotency not in {"supported", "required"}:
        fail("ACTION_SIDE_EFFECT_CONFLICT", "idempotent retry 需要幂等支持")
    if side_effect == "destructive" and (not approval_required or retry_policy != "none" or agent_callable):
        fail("ACTION_SIDE_EFFECT_CONFLICT", "destructive 必须审批、禁止重试且不可 agent-callable")

    exposure_raw = fields.get("exposure", "internal")
    exposure = parse_list(exposure_raw, "exposure", re.compile(r"^(?:internal|api|agent)$"))
    if not exposure:
        fail("ACTION_ENUM_INVALID", "exposure 不能为空")
    if "internal" in exposure and len(exposure) > 1:
        fail("ACTION_CALLABLE_CONFLICT", "internal 不能与 api/agent 并存")
    if exposure == ["agent", "api"] and exposure_raw != "api,agent":
        fail("ACTION_ENUM_INVALID", "api 与 agent 并存时 exposure 必须写为 api,agent")
    if agent_callable and (interaction not in {"requestReply", "oneWayProducer"} or "agent" not in exposure):
        fail("ACTION_CALLABLE_CONFLICT", "agent-callable 与交互模式或 exposure 冲突")

    required_config = parse_list(fields.get("required-config-keys", ""), "required-config-keys", NAME_RE)
    credentials = parse_list(fields.get("credential-aliases", ""), "credential-aliases", NAME_RE)
    scopes = parse_list(fields.get("required-scopes", ""), "required-scopes", SCOPE_RE)
    for key in required_config:
        if key not in merged_config:
            fail("ACTION_CONFIG_REFERENCE_MISSING", f"所需配置 key 不存在：{key}")

    metadata = route_metadata(route)
    input_contract = schema_descriptor(service_dir, metadata, "input")
    output_contract = schema_descriptor(service_dir, metadata, "output")
    error_contract = schema_descriptor(service_dir, metadata, "error")
    validate_interaction_contracts(interaction, input_contract, output_contract)
    validate_contract_stage(route, input_contract)

    entry = route_from(route)
    uri = (entry.get("uri") or "").strip()
    scheme = endpoint_scheme(uri)
    validate_endpoint_profile(route, scheme, interaction)
    uri_template = safe_uri_template(uri, scheme)
    methods, http_path = http_details(uri, scheme)

    error_sources: list[str] = []
    route_configuration = (route.get("routeConfigurationId") or "").strip()
    if route_configuration:
        if not NAME_RE.fullmatch(route_configuration):
            fail("ACTION_ROUTE_METADATA_INVALID", "routeConfigurationId 非法")
        error_sources.append(f"routeConfiguration:{route_configuration}")
    if any(local_name(element.tag) == "doCatch" for element in route.iter()):
        error_sources.append("doCatch")

    normalized_fields: dict[str, Any] = {
        "actionId": action_id,
        "agentCallable": agent_callable,
        "approvalRequired": approval_required,
        "credentialAliases": credentials,
        "description": description,
        "exposure": exposure,
        "idempotency": idempotency,
        "interactionPattern": interaction,
        "name": name,
        "requiredConfigKeys": required_config,
        "requiredScopes": scopes,
        "retryPolicy": retry_policy,
        "routeId": route_id,
        "sideEffect": side_effect,
    }
    source_locations = {"common.config.properties", "service.config.properties", route_file.name}
    for contract in (input_contract, output_contract, error_contract):
        if contract:
            source_locations.add(contract["schema"])

    service_impl = merged_config.get("service.impl", "REST").strip() or "REST"
    service_type = merged_config.get("service.type", service_impl).strip() or service_impl
    if not NAME_RE.fullmatch(service_impl) or not NAME_RE.fullmatch(service_type):
        fail("ACTION_FIELD_UNKNOWN", "service.impl/service.type 格式非法")
    service_tags = parse_list(merged_config.get("service.tags", ""), "service.tags", NAME_RE)
    service_description = merged_config.get("service.description", "").strip()
    service_provider = merged_config.get("service.provider", "").strip()
    reject_sensitive_text(service_description, "service.description")
    reject_sensitive_text(service_provider, "service.provider")
    digest_fields = {
        **normalized_fields,
        "serviceDescription": service_description,
        "serviceImpl": service_impl,
        "serviceName": service_dir.parent.name,
        "serviceProvider": service_provider,
        "serviceTags": service_tags,
        "serviceType": service_type,
        "serviceVersion": service_dir.name,
    }
    return {
        **normalized_fields,
        "entry": {
            "httpMethods": methods,
            "httpPath": http_path,
            "uriTemplate": uri_template,
        },
        "errorContract": error_contract,
        "errorHandling": {
            "sources": sorted(error_sources),
            "status": "declared" if error_sources else "noneDeclared",
        },
        "inputContract": input_contract,
        "outboundSteps": outbound_steps(route),
        "outputContract": output_contract,
        "protocol": scheme,
        "serviceDescription": service_description,
        "serviceImpl": service_impl,
        "serviceName": service_dir.parent.name,
        "serviceProvider": service_provider,
        "serviceTags": service_tags,
        "serviceType": service_type,
        "serviceVersion": service_dir.name,
        "sourceDigest": source_digest(digest_fields, route, [input_contract, output_contract, error_contract]),
        "sourceLocations": sorted(source_locations),
        "validationStatus": "valid",
    }


def analyze_service(service_dir: Path, *, explicit: bool) -> list[dict[str, Any]]:
    reject_symlink(service_dir)
    if not service_dir.is_dir():
        fail("ACTION_SOURCE_UNSAFE", f"服务目录不存在：{service_dir}")
    common_path = service_dir / "common.config.properties"
    service_path = service_dir / "service.config.properties"
    common = parse_properties(common_path, allow_action=False)
    service = parse_properties(service_path, allow_action=True)
    has_action_declaration = bool(service.action_keys)
    if not has_action_declaration and not explicit:
        return []
    if service.values.get("actions.schema-version") != DECLARATION_SCHEMA_VERSION:
        fail("ACTION_DECLARATION_VERSION_INVALID", "缺少或不支持 actions.schema-version")
    ids_raw = service.values.get("actions.ids")
    if ids_raw is None or ids_raw.strip() == "":
        fail("ACTION_LIST_MISSING", "缺少或为空 actions.ids")
    action_ids = parse_action_ids(ids_raw)
    if len(action_ids) > MAX_ACTIONS_PER_SERVICE:
        fail("ACTION_LIMIT_EXCEEDED", "单服务 Action 数量超限")

    merged = dict(common.values)
    merged.update(service.values)
    expected_name = service_dir.parent.name
    expected_version = service_dir.name
    if service.values.get("service.name", expected_name).strip() != expected_name:
        fail("ACTION_SERVICE_IDENTITY_CONFLICT", "service.name 与目录不一致")
    if service.values.get("service.version", expected_version).strip() != expected_version:
        fail("ACTION_SERVICE_IDENTITY_CONFLICT", "service.version 与目录不一致")
    if not NAME_RE.fullmatch(expected_name) or not NAME_RE.fullmatch(expected_version):
        fail("ACTION_SERVICE_IDENTITY_CONFLICT", "serviceName/serviceVersion 目录格式非法")
    for key in service.action_keys:
        if key.startswith("actions.") and key not in {"actions.schema-version", "actions.ids"}:
            fail("ACTION_FIELD_UNKNOWN", f"未知 Action 顶层字段：{key}")

    xml_files: list[Path] = []
    for child in limited_children(service_dir, MAX_SERVICE_ENTRIES):
        reject_symlink(child)
        if child.is_file() and child.suffix.lower() == ".xml":
            xml_files.append(child)
    if len(xml_files) != 1:
        fail("ACTION_ROUTE_NOT_FOUND", f"服务版本目录必须恰有一个 XML，实际 {len(xml_files)}")
    route_file = xml_files[0]
    xml_text = read_limited(route_file, MAX_XML_BYTES, "route XML")
    if re.search(r"<!DOCTYPE|<!ENTITY", xml_text, flags=re.IGNORECASE):
        fail("ACTION_SOURCE_UNSAFE", "route XML 禁止 DOCTYPE/ENTITY")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        fail("ACTION_SOURCE_UNSAFE", f"route XML 无法解析：{exc}")
    for key in sorted(set(PLACEHOLDER_RE.findall(xml_text))):
        if not key.startswith("env:") and key not in merged:
            fail("ACTION_CONFIG_REFERENCE_MISSING", f"XML 占位符无配置来源：{key}")

    routes: dict[str, ET.Element] = {}
    all_routes: list[ET.Element] = [element for element in root.iter() if local_name(element.tag) == "route"]
    for route in all_routes:
        route_id = (route.get("id") or "").strip()
        if not route_id or not NAME_RE.fullmatch(route_id) or route_id in routes:
            fail("ACTION_ROUTE_NOT_FOUND", "route id 缺失或重复")
        routes[route_id] = route

    bound_routes: set[str] = set()
    actions: list[dict[str, Any]] = []
    for action_id in action_ids:
        if len(action_id) > 64 or not ACTION_ID_RE.fullmatch(action_id):
            fail("ACTION_ID_INVALID", f"actionId 非法：{action_id}")
        fields = parse_action_fields(action_id, service)
        route_id = require_scalar(fields, "route-id")
        route = routes.get(route_id)
        if route is None:
            fail("ACTION_ROUTE_NOT_FOUND", f"route 不存在：{route_id}")
        if route_id in bound_routes:
            fail("ACTION_ROUTE_BINDING_CONFLICT", f"多个 Action 绑定同一 route：{route_id}")
        bound_routes.add(route_id)
        actions.append(analyze_action(service_dir, route_file, route, action_id, fields, merged))

    for route_id, route in routes.items():
        has_metadata = any(
            local_name(child.tag) == "routeProperty"
            and (child.get("key") or "").startswith("lightesb.action.")
            for child in list(route)
        )
        if has_metadata and route_id not in bound_routes:
            fail("ACTION_ROUTE_BINDING_CONFLICT", f"route metadata 未绑定 Action：{route_id}")
    return actions


def discover_services(app_root: Path) -> list[Path]:
    reject_symlink(app_root)
    if not app_root.is_dir():
        fail("ACTION_SOURCE_UNSAFE", "app root 不存在")
    service_dirs: list[Path] = []
    for service_name in limited_children(app_root, MAX_ROOT_ENTRIES):
        reject_symlink(service_name)
        if service_name.is_file():
            continue
        if not service_name.is_dir():
            fail("ACTION_SOURCE_UNSAFE", f"app root 存在非法条目：{service_name.name}")
        for version in limited_children(service_name, MAX_ROOT_ENTRIES):
            reject_symlink(version)
            if not version.is_dir():
                fail("ACTION_SOURCE_UNSAFE", f"服务目录必须严格为两层：{service_name.name}/{version.name}")
            service_dirs.append(version)
            if len(service_dirs) > MAX_SERVICES:
                fail("ACTION_LIMIT_EXCEEDED", "服务数量超限")
    return service_dirs


def validate_index_shape(index: dict[str, Any]) -> None:
    if set(index) != {"actions", "schemaVersion"} or index.get("schemaVersion") != CATALOG_SCHEMA_VERSION:
        fail("ACTION_SOURCE_UNSAFE", "内部索引顶层结构与 schema 不一致")
    required = {
        "actionId", "agentCallable", "approvalRequired", "credentialAliases", "description",
        "entry", "errorContract", "errorHandling", "exposure", "idempotency", "inputContract",
        "interactionPattern", "name", "outboundSteps", "outputContract", "protocol",
        "requiredConfigKeys", "requiredScopes", "retryPolicy", "routeId", "serviceDescription",
        "serviceImpl", "serviceName", "serviceProvider", "serviceTags", "serviceType",
        "serviceVersion", "sideEffect", "sourceDigest", "sourceLocations", "validationStatus",
    }
    for action in index["actions"]:
        if set(action) != required:
            fail("ACTION_SOURCE_UNSAFE", "内部 Action 输出字段与 schema 不一致")


def validate_output_path(output: Path, service_dirs: list[Path]) -> Path:
    for candidate in (output, *output.parents):
        if candidate.exists() and candidate.is_symlink():
            fail("ACTION_SOURCE_UNSAFE", "输出路径不能经过 symlink")
    resolved = output.absolute().resolve(strict=False)
    for service_dir in service_dirs:
        if is_within(resolved, service_dir.resolve()):
            fail("ACTION_SOURCE_UNSAFE", "输出文件不能位于服务版本目录内")
    return resolved


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def build_catalog(service_dirs: list[Path], *, explicit: bool) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    unique_keys: set[tuple[str, str]] = set()
    for service_dir in service_dirs:
        for action in analyze_service(service_dir, explicit=explicit):
            key = (action["actionId"], action["serviceVersion"])
            if key in unique_keys:
                fail("ACTION_DECLARATION_DUPLICATE", f"actionId + serviceVersion 冲突：{key[0]}/{key[1]}")
            unique_keys.add(key)
            actions.append(action)
            if len(actions) > MAX_ACTIONS:
                fail("ACTION_LIMIT_EXCEEDED", "Action 总数超限")
    actions.sort(key=lambda item: (item["actionId"], item["serviceVersion"]))
    index = {"actions": actions, "schemaVersion": CATALOG_SCHEMA_VERSION}
    validate_index_shape(index)
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="从 LightESB 服务目录生成确定性 Action catalog")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--service-dir", type=Path, help="显式校验一个 {serviceName}/{serviceVersion} 目录")
    source.add_argument("--app-root", type=Path, help="批量扫描严格的 {serviceName}/{serviceVersion} 两层目录")
    parser.add_argument("--output", type=Path, help="输出到服务目录外的文件；省略时写 stdout")
    args = parser.parse_args()

    try:
        if args.service_dir:
            service_dirs = [args.service_dir.absolute()]
            explicit = True
        else:
            service_dirs = discover_services(args.app_root.absolute())
            explicit = False
        index = build_catalog(service_dirs, explicit=explicit)
        content = json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        if args.output:
            output = validate_output_path(args.output, service_dirs)
            write_atomic(output, content)
        else:
            sys.stdout.write(content)
        return 0
    except CatalogError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
