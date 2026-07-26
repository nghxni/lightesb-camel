#!/usr/bin/env python3
"""Offline static preflight for a LightESB service route directory.

It deliberately does not start LightESB, connect to an endpoint, or resolve
environment variables. It checks the configuration closure observable from a
service directory before runtime validation is explicitly authorized.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PROFILE_REQUIREMENTS = {
    "externaldb": {
        "properties": ["HTTP.Listener", "system.components", "extdb.enabled", "extdb.default", "extdb.ids", "extdb.primary.url", "extdb.primary.username", "extdb.primary.password"],
        "components": ["externaldb"], "values": {"HTTP.Listener": "false"}, "xml": [r"sql:", r"extdb-\{\{extdb\.default\}\}-datasource"],
    },
    "mqtt": {
        "properties": ["HTTP.Listener", "server.running", "system.components", "industrial.mqtt.broker.url", "industrial.mqtt.username", "industrial.mqtt.password"],
        "components": ["industrial"], "values": {"HTTP.Listener": "false", "server.running": "false"}, "xml": [r"mqtt:"],
    },
    "opcua": {
        "properties": ["HTTP.Listener", "server.running", "system.components", "industrial.opcua.endpoint.uri", "industrial.opcua.username", "industrial.opcua.password"],
        "components": ["industrial"], "values": {"HTTP.Listener": "false", "server.running": "false"}, "xml": [r"opcua:"],
    },
    "modbus": {
        "properties": ["HTTP.Listener", "server.running", "system.components", "industrial.modbus.host", "industrial.modbus.port", "industrial.modbus.unitId", "industrial.modbus.address"],
        "components": ["industrial"], "values": {"HTTP.Listener": "false", "server.running": "false"}, "xml": [r"modbus:"],
    },
    "http": {"properties": ["HTTP.Listener", "server.port", "system.components"], "components": ["undertowhttp"], "values": {"HTTP.Listener": "true"}, "xml": [r"undertow:"]},
    "timer": {"properties": ["HTTP.Listener"], "components": [], "values": {"HTTP.Listener": "false"}, "xml": [r"timer:" ]},
    "transform": {"properties": ["HTTP.Listener", "server.port", "system.components", "input-transform", "input-transform.file"], "components": ["undertowhttp", "jsontransform", "conditionaltransform"], "values": {"HTTP.Listener": "true"}, "xml": [r"undertow:", r"conditionaltransform:"]},
    "schema": {"properties": ["HTTP.Listener", "server.port", "system.components"], "components": ["undertowhttp"], "values": {"HTTP.Listener": "true"}, "xml": [r"undertow:", r"JsonSchemaPath", r"JsonSchemaValidationMode", r"jsonSchemaValidationProcessor"]},
    "ai-agent": {"properties": ["HTTP.Listener", "server.port", "system.components", "service.ai.route", "service.ai.type", "service.ai.mode", "ai.agent.tags"], "components": ["undertowhttp"], "values": {"HTTP.Listener": "true", "service.ai.mode": "agent"}, "xml": [r"undertow:", r"langchain4j-agent", r"langchain4j-tools"]},
    "sap-mock": {"properties": ["HTTP.Listener", "server.port", "system.components"], "components": ["undertowhttp"], "values": {"HTTP.Listener": "true"}, "xml": [r"undertow:"]},
}


def parse_properties(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(("#", "!")):
            continue
        match = re.match(r"([^=:\s]+)\s*(?:=|:)\s*(.*)$", line)
        if not match:
            raise ValueError(f"{path.name}:{number} 不是 key=value 或 key:value")
        values[match.group(1)] = match.group(2).strip()
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="LightESB 服务目录离线静态预检")
    parser.add_argument("--service-dir", required=True, type=Path, help="服务版本目录")
    parser.add_argument("--profile", choices=sorted(PROFILE_REQUIREMENTS), default="http")
    parser.add_argument("--route-file", help="期望的唯一 XML 文件名；省略时要求目录中恰有一个 XML")
    args = parser.parse_args()
    service_dir = args.service_dir.resolve()
    errors: list[str] = []
    if not service_dir.is_dir():
        print(f"FAIL service directory not found: {service_dir}")
        return 2

    xml_files = sorted(service_dir.glob("*.xml"))
    route_path: Path | None
    if args.route_file:
        route_path = service_dir / args.route_file
        if not route_path.is_file():
            errors.append(f"缺少 route XML：{args.route_file}")
    elif len(xml_files) != 1:
        errors.append(f"应恰有一个 route XML，实际为 {len(xml_files)} 个")
        route_path = xml_files[0] if xml_files else None
    else:
        route_path = xml_files[0]

    configs: dict[str, str] = {}
    for name in ("common.config.properties", "service.config.properties"):
        path = service_dir / name
        if not path.is_file():
            errors.append(f"缺少配置文件：{name}")
            continue
        try:
            configs.update(parse_properties(path))
        except ValueError as exc:
            errors.append(str(exc))

    for key in ("service.name", "service.version"):
        if key not in configs:
            errors.append(f"缺少通用配置键：{key}")
    profile = PROFILE_REQUIREMENTS[args.profile]
    for key in profile["properties"]:
        if key not in configs:
            errors.append(f"[{args.profile}] 缺少配置键：{key}")
    for key, expected in profile.get("values", {}).items():
        if key in configs and configs[key].lower() != expected:
            errors.append(f"[{args.profile}] 配置值必须为 {key}={expected}")
    components = {item.strip() for item in configs.get("system.components", "").split(",") if item.strip()}
    for component in profile["components"]:
        if component not in components:
            errors.append(f"[{args.profile}] system.components 缺少：{component}")

    if route_path and route_path.is_file():
        xml = route_path.read_text(encoding="utf-8")
        try:
            ET.fromstring(xml)
        except ET.ParseError as exc:
            errors.append(f"route XML 无法解析：{exc}")
        for key in sorted(set(re.findall(r"\{\{\s*([^{}]+?)\s*\}\}", xml))):
            if not key.startswith("env:") and key not in configs:
                errors.append(f"XML 占位符无配置来源：{key}")
        for pattern in profile["xml"]:
            if not re.search(pattern, xml, flags=re.IGNORECASE):
                errors.append(f"[{args.profile}] XML 缺少必要模式：{pattern}")
        for resource in sorted(set(re.findall(r"(?:[\w.-]+/)*[\w.-]+\.(?:ds|json)", xml))):
            if not (service_dir / resource).is_file():
                errors.append(f"XML 引用资源不存在：{resource}")
        if args.profile == "sap-mock" and re.search(r"sap-netweaver:", xml, flags=re.IGNORECASE):
            errors.append("[sap-mock] 不应使用 sap-netweaver: endpoint")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS profile={args.profile} route={route_path.name if route_path else '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
