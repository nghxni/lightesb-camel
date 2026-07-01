# LightESB-Camel 组件文档索引

本文档按交付使用顺序组织。源码仓库原始文档保持编号；本交付包文档按场景重排，并在 `SOURCE_MAP.md` 中维护来源映射。

## 项目入口

- [仓库 README](../README.md)：项目定位、能力矩阵、快速启动、目录结构、Support 和 License。
- [Agent 规则](../AGENTS.md)：Agent 在本交付包内工作的约束。
- [Claude 入口](../CLAUDE.md)：Claude/Codex 类 Agent 的简版阅读入口。

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

## 机器人、企业系统、工业协议与扩展

- [ExternalDB 数据访问](components/11-externaldb.md)
- [AI Chat 组件](components/12-ai-chat.md)
- [SAP NetWeaver 组件](components/13-sap-netweaver.md)
- [AVEVA Plant SCADA OPC UA / MQTT 接入](components/15-aveva-plant-scada-opcua-mqtt.md)
- [DTS 扩展开发指南](extensions/01-dts-extension-guide.md)
- [DTS 最小模板](extensions/02-dts-minimal-template.md)

## 经验沉淀

- [机器人协议接入前置验证](experience/01-robotics-protocol-precheck.md)
- [机器人协议接入正确做法](experience/02-robotics-protocol-correct-practices.md)
- 机器人/ROS/PLC 场景以“动态热加载路由技能”和“核心能力全链路功能服务”为交付口径，覆盖 MQTT、rosbridge、OPC UA、Modbus TCP、PLC4X 评估路径、Kafka 风格出流和 gRPC 契约；技能包可用 `server.running=false` 保留但不加载，需要时通过 CLI 启停、部署或重载；真实现场执行按 mock-first / local baseline / field validation 分层验收。

## CLI 自动化

- [LightESB CLI 使用参考](cli/README.md)
- [CLI 命令压缩参考](cli/01-cli-command-reference.md)
- [管理 API 响应契约](api-response-contract.md)
- [部署管理 API](deployment-management-api.md)
- [AI 路由缓存管理 API](ai-route-cache-api.md)
- [运行时诊断 API 与 CLI](runtime-diagnostics-api.md)
- [机器人命令 dispatcher API](robot-command-dispatcher-api.md)

## 样例

- [example 样例索引](../example/README.md)
- 转换综合演示见 `../example/routes/PlatformHttp/`。
- HTTP 内部转发演示见 `../example/routes/HttpRequestSrv/v1.0.0/`。
- Timer 定时任务演示见 `../example/routes/timer/`。
- ExternalDB MySQL 演示见 `../example/routes/MysqlRouteSrv/v1.0.0/`。
- DTS Java SPI 扩展示例见 `../example/transform-dts-java/`。
- AI Agent + Tools 演示见 `../example/routes/AiAgentDemoSrv/v1.0.0/`。
- `example/routes/**` 是可复制运行的交付样例；AI 路由生成依据自然语言需求和本交付包 docs/skills/examples 上下文判断组件与配置，不维护源码临时模板目录。

## Skill 路由

| 任务 | Skill |
| --- | --- |
| 路由和 HTTP 接口 | `../skills/lightesb-route-authoring/SKILL.md` |
| 转换组件 | `../skills/lightesb-transform-components/SKILL.md` |
| 权限与校验 | `../skills/lightesb-security-validation/SKILL.md` |
| 日志、异常、缓存 | `../skills/lightesb-logging-observability/SKILL.md` |
| DTS 扩展 | `../skills/lightesb-dts-extension/SKILL.md` |
| AI、机器人和外部系统扩展 | `../skills/lightesb-ai-components/SKILL.md` |
| CLI 命令和自动化流程 | `../skills/lightesb-cli-automation/SKILL.md` |
| 机器人协议样例、命令 dispatcher 和现场验收边界 | `../skills/lightesb-robot-integration/SKILL.md` |

## 明确不包含

本交付包只包含本索引列出的组件级技术上下文；未随包交付的内部材料不作为 Agent 工作依据。
