# 轻量 Camel 接口管理

本目录是 LightESB-Camel 的完整可运行交付物，不是完整源码仓库。`lightesb-camel-1.0.0.jar` 是核心运行件，`start.sh` / `start.bat`、`lightesb-camel-app/`、`docs/`、`example/`、`skills/` 和 `AGENTS.md` 共同构成交付上下文。

使用 JDK21 + Apache Camel 4.18.x 构建的轻量 ESB 接口管理与监控平台，支持 AI Agent 模式，可直接复用存量系统 API。

核心能力：
- HTTP 接口暴露与服务编排（Undertow、Route Loader 生命周期）
- 统一日志、动态日志调级与链路观测（CamelServiceLog、指标采集）
- 数据转换与校验（ConditionalTransform、JsonTransform、JSON Schema）
- 安全与权限（IP/CIDR/Token 校验、核心安全包约束）
- 数据访问与缓存（ExternalDB、多数据源、H2 缓存与关键字检索）
- 异常兜底与全局处理链
- AI 扩展能力（LangChain4j + Camel、AI Chat 框架）
- 第三方 DTS SPI 扩展接入与最小模板落地

## 快速启动

```bash
./start.sh
```

Windows 环境使用：

```bat
start.bat
```

运行服务、样例验证和日志查看以 [docs/README.md](docs/README.md) 与 [example/README.md](example/README.md) 为准。

## Agent 使用入口

Codex 或其他 Agent 在本目录内工作时，先读 [AGENTS.md](AGENTS.md)，再读 [docs/README.md](docs/README.md)。

当任务命中某个组件领域时，必须先读项目内对应的 `skills/<name>/SKILL.md`，再查组件文档和样例：

- 路由和 HTTP 接口：`skills/lightesb-route-authoring/SKILL.md`
- 转换组件：`skills/lightesb-transform-components/SKILL.md`
- 权限与校验：`skills/lightesb-security-validation/SKILL.md`
- 日志、异常、缓存：`skills/lightesb-logging-observability/SKILL.md`
- DTS 扩展：`skills/lightesb-dts-extension/SKILL.md`
- AI 和外部系统扩展：`skills/lightesb-ai-components/SKILL.md`
- CLI 命令和自动化流程：`skills/lightesb-cli-automation/SKILL.md`

默认优先修改 `example/` 中的演示样例。`lightesb-camel-app/` 是正式接口运行目录，除非明确需要验证运行，不在其中新增索引、说明或 Agent 上下文文件。



# lightesb-camel
A lightweight ESB interface management and monitoring platform built on Apache Camel. It supports AI Agent mode and can directly reuse APIs from legacy systems.

Key capabilities :
- HTTP exposure and service orchestration (Undertow, route loader lifecycle)
- Unified logging, dynamic log level control, and observability (CamelServiceLog, metrics collector)
- Data transform and validation (ConditionalTransform, JsonTransform, JSON Schema)
- Security and access control (IP/CIDR/Token checks, core secure package rules)
- Data access and cache flow (ExternalDB, multi-datasource, H2 cache + keyword search)
- Global exception fallback chain
- AI integration (LangChain4j + Camel, AI chat framework)
- Third-party DTS SPI extension and minimal template
