# LightESB-Camel 组件文档索引

本文档按交付使用顺序组织。源码仓库原始文档保持编号；本交付包文档按场景重排，并在 `SOURCE_MAP.md` 中维护来源映射。

本目录是完整可运行交付物的一部分，根目录 `lightesb-camel-1.0.0.jar` 是核心运行件。Agent 使用时先读根目录 `AGENTS.md`，再按本文档索引进入组件文档、样例和项目内 `skills/`。

## 快速开始

- [HTTP 入口与路由基础](components/01-http-route-basics.md)
- [服务日志 servicelog](components/02-service-log.md)
- [字符编码处理](components/03-charset-processing.md)
- [Timer 定时路由](components/14-timer-routes.md)

## 数据处理

- [条件转换与 JSON 转换](components/04-transform-components.md)
- [JSON Schema 校验](components/05-json-schema-validation.md)
- [JsonKeyword 外发版](components/06-json-keyword.md)
- [StreamCache 流缓存](components/07-stream-cache.md)

## 安全与治理

- [权限校验](components/08-permission-validation.md)
- [异常处理与错误响应](components/09-exception-handling.md)
- [H2 缓存与 JsonKeyword 链路](components/10-h2-jsonkeyword-chain.md)

## 数据访问与扩展

- [ExternalDB 数据访问](components/11-externaldb.md)
- [AI Chat 组件](components/12-ai-chat.md)
- [SAP NetWeaver 组件](components/13-sap-netweaver.md)
- [DTS 扩展开发指南](extensions/01-dts-extension-guide.md)
- [DTS 最小模板](extensions/02-dts-minimal-template.md)

## CLI 自动化

- [LightESB CLI 使用参考](cli/README.md)
- [CLI 命令压缩参考](cli/01-cli-command-reference.md)

## 样例

- [example 样例索引](../example/README.md)
- 转换综合演示见 `../example/routes/PlatformHttp/`。
- HTTP 内部转发演示见 `../example/routes/HttpRequestSrv/v1.0.0/`。
- Timer 定时任务演示见 `../example/routes/timer/`。
- ExternalDB MySQL 演示见 `../example/routes/MysqlRouteSrv/v1.0.0/`。
- DTS Java SPI 扩展示例见 `../example/transform-dts-java/`。
- AI Agent + Tools 演示见 `../example/routes/AiAgentDemoSrv/v1.0.0/`。

## Skill 路由

`../skills/` 是本交付包内的任务路由卡片。任务命中时，先读对应 `SKILL.md`，再读下方组件文档和样例。

| 任务 | Skill |
| --- | --- |
| 路由和 HTTP 接口 | `../skills/lightesb-route-authoring/SKILL.md` |
| 转换组件 | `../skills/lightesb-transform-components/SKILL.md` |
| 权限与校验 | `../skills/lightesb-security-validation/SKILL.md` |
| 日志、异常、缓存 | `../skills/lightesb-logging-observability/SKILL.md` |
| DTS 扩展 | `../skills/lightesb-dts-extension/SKILL.md` |
| AI 和外部系统扩展 | `../skills/lightesb-ai-components/SKILL.md` |
| CLI 命令和自动化流程 | `../skills/lightesb-cli-automation/SKILL.md` |

## 明确不包含

本交付包只包含本索引列出的组件级技术上下文；未随包交付的内部材料不作为 Agent 工作依据。
