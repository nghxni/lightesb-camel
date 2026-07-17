# LightESB-Camel Product Overview

LightESB-Camel is a runnable Apache Camel delivery package for integration teams that need to connect legacy systems, industrial protocols, robotics workflows, and AI-assisted orchestration without rewriting core business systems.

It packages a practical integration runtime, documented route examples, CLI automation, operational guardrails, and Agent-readable component guidance into a delivery repository that can be used for local validation, POC work, and field implementation.

## What It Is

LightESB-Camel is the delivery form of LightESB's integration runtime. It focuses on:

- Hot-loadable Camel route services.
- Service package conventions for repeatable deployment.
- HTTP, database, messaging, industrial, robotics, and AI integration examples.
- CLI and management API workflows for deployment, diagnostics, logs, and route operations.
- Agent-friendly documentation and skills for route authoring, troubleshooting, and integration tasks.

It is not the full internal source repository. Public users should treat this repository as a runnable delivery package with examples, documentation, and operational context.

## Who It Is For

LightESB-Camel is designed for:

- Integration engineers modernizing legacy HTTP, database, message, ERP, MES, WMS, or industrial interfaces.
- Solution architects who need a lightweight ESB-style runtime for private or edge deployment.
- Industrial automation teams connecting OPC UA, MQTT, Modbus, PLC gateways, AVEVA Plant SCADA, or SAP NetWeaver.
- Robotics teams that need governed task intake, telemetry normalization, command validation, audit trails, and protocol gateway examples.
- AI and automation teams that want AI Agent + Tools orchestration around existing systems and route services.

## Core Capabilities

| Capability | Delivery Content |
| --- | --- |
| Route service runtime | Apache Camel XML routes, service directories, hot loading, and route lifecycle guidance |
| Legacy integration | HTTP ingress, internal HTTP forwarding, database access, JSON transformation, schema validation, and error handling |
| Industrial connectivity | OPC UA, MQTT 5, Modbus/PLC gateway examples, AVEVA Plant SCADA, SAP NetWeaver, and ExternalDB patterns |
| Robotics integration | MQTT telemetry and command routes, rosbridge examples, Modbus and OPC UA station examples, dispatcher API docs, and robot command proto |
| AI-assisted orchestration | AI Agent + Tools component guidance for request building, tool calling, and operational workflows |
| Operations and governance | CLI automation, deployment management API, diagnostics API, service logs, permission checks, and audit-oriented patterns |
| Agent context | Skills, examples, and documentation that external coding agents can use to author or adapt route services |

## Integration Model

LightESB-Camel uses a service package model:

```text
lightesb-camel-app/{serviceName}/{serviceVersion}/
├── common.config.properties
├── service.config.properties
└── one-route-file.xml
```

Each service version contains exactly one Camel XML route file, which may define multiple route IDs. Each service package can be copied from `example/routes/**`, adjusted through configuration and Camel XML, and then loaded by the runtime. Route-level changes can be hot-loaded when they stay within the service package boundary. Java code, dependencies, Spring beans, and startup parameters still require a rebuild or restart.

## Robotics Boundary

LightESB-Camel is intended for high-level robotics integration, not hard real-time control.

It can help with:

- Task intake from MES, WMS, ERP, scheduling systems, or AI tools.
- Command validation and idempotency.
- Telemetry normalization and event routing.
- MQTT, rosbridge, OPC UA, Modbus, and gateway-oriented protocol examples.
- Audit trails and operational diagnostics.

It does not replace:

- Servo loops.
- Motion planning safety systems.
- PLC safety circuits.
- ROS2 DDS high-frequency control paths.
- Emergency stop or certified safety functions.

## Recommended Reading Path

1. Start with the repository [README](../README.md).
2. Review the component and workflow index in [docs/README.md](README.md).
3. Pick a runnable example from [example/README.md](../example/README.md).
4. Use the CLI guide in [docs/cli/README.md](cli/README.md) for deployment and diagnostics.
5. For robotics work, read [robot-command-dispatcher-api.md](robot-command-dispatcher-api.md) and the robotics experience notes under `docs/experience/`.

## Hosting and Website

The public English website should be generated from this delivery context. The recommended static site source is `website/`, deployed from the public delivery repository with Cloudflare Pages:

```text
Root directory: website
Build command: npm run build
Build output directory: dist
```

The website should describe the delivery package in English, link back to runnable examples and documentation, and avoid internal source repository paths or development-only materials.

## Support Boundary

This repository is suitable for community self-validation and POC exploration. POC support, implementation services, SLA commitments, private deployment support, and field integration assistance are optional commercial support scopes defined separately.
