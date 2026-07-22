# LightESB-Camel

**Website:** [https://lightesb-camel.pages.dev](https://lightesb-camel.pages.dev)

**Target users:** integration architects, Java and Apache Camel engineers, manufacturing IT teams, automation and robotics integration teams, solution delivery engineers, and coding agents that need runnable examples for legacy system and industrial protocol integration.

LightESB-Camel is a runnable Apache Camel delivery package for teams that need to connect legacy applications, industrial protocols, robot workflow systems, and AI-assisted orchestration without replacing existing core systems. It packages runtime artifacts, route examples, documentation, CLI guidance, and agent-readable skills so a delivery team can copy examples, adapt configuration, validate behavior, and move from POC to field verification.

## 中文概述

LightESB-Camel 是 LightESB 的可运行 Camel 交付包。LightESB 是一个轻量集成平台，面向存量系统接入，并为机器人系统提供动态热加载的技能扩展能力。

LightESB 聚焦三件事：

- 接入老系统接口和机器人自动化业务流程。
- 给机器人提供更多、更自由的动态扩展能力。
- 集成适配机器人核心能力的全链路功能服务。

一句话介绍：LightESB-Camel 是面向存量系统和机器人系统的轻量集成交付包，用动态热加载路由技能连接老系统接口、工业协议、机器人任务流程和 AI Agent 工具能力。

本仓库不是完整源码仓库。根目录的 `lightesb-camel-1.0.0.jar`、`lightesb-cli.jar`、`start.sh` / `start.bat`、`lightesb-camel-app/`、`docs/`、`example/`、`skills/`、`AGENTS.md` 共同构成交付上下文。外部 Agent 或大模型只读取本仓库时，应优先从本 README、`AGENTS.md`、`docs/README.md` 和 `example/README.md` 建立上下文。

相比直接使用原生 Apache Camel，本交付包已经封装了启动脚本、服务目录约定、CLI 管理入口、组件文档和可复制样例。常见 HTTP 接入、字段映射、条件转换、校验、日志和协议适配流程优先通过 Camel XML 路由和配置文件表达，适合先用样例完成 POC，再按服务包方式进入交付验证。

## 核心能力

| 能力 | 交付内容 |
| --- | --- |
| 存量系统与机器人流程接入 | Apache Camel XML 路由、Undertow HTTP 入口、老系统接口整合、机器人自动化业务流程编排 |
| 动态热加载路由技能 | 轻量路由技能包、服务目录加载、`server.running=false` 按需禁用、CLI 启停/部署/重载、DTS Java SPI 扩展、AI Agent + Tools 编排 |
| 机器人核心能力全链路服务 | MQTT telemetry/command、rosbridge/ROS 管理面、OPC UA、Modbus/PLC、Kafka 风格数据管道、gRPC 契约草案 |
| 数据转换与校验 | ConditionalTransform、JsonTransform、DataSonnet、JSON Schema 校验、DTS Java SPI 扩展 |
| 安全与治理 | IP/CIDR/Token/Regex 权限校验、全局异常响应、服务日志、H2 缓存和关键字检索 |
| 企业系统与工业协议适配 | ExternalDB 多数据源、SAP NetWeaver、AVEVA Plant SCADA、OPC UA、MQTT 5、Modbus/PLC 接入、PLC4X 评估路径 |
| 自动化运维 | LightESB CLI、部署管理 API、运行时诊断 API、服务状态查询、日志查看、样例验证流程 |
| AI 集成 | AI Agent + Tools、面向接口编排、技能生成和运维问答的组件上下文 |

边界说明：LightESB 面向管理面、集成面和任务流程编排，不替代机器人实时控制器、PLC 安全回路、ROS2 DDS 高频链路或硬件急停系统。路由 XML、配置和服务包类技能可热加载；Java 代码、依赖、Spring Bean 或启动参数变化仍需要重新打包或重启。

## 适用场景

- 存量 HTTP、数据库、消息、企业系统、工业协议、机器人/ROS 或第三方系统接口整合。
- 机器人自动化业务流程编排，包括任务接入、遥测标准化、命令预检、结果回执、审计和外部系统回调。
- 机器人技能或适配能力的动态扩展：通过轻量路由技能包、Camel 路由、配置文件和可选扩展组件，在不重构主系统的前提下新增能力。
- 在 Camel 路由中完成字段映射、条件转换、schema 校验、权限控制和统一错误响应。
- 面向制造、工厂自动化和机器人集成场景，承接 OPC UA、MQTT 5、Modbus/PLC、rosbridge/ROS、Kafka 风格数据出流和外部任务接入的适配、验证和交付。
- 部署在本地服务器、工控机或边缘节点，用于承接现场系统、设备协议、机器人任务和上层业务系统之间的接口转换与流程编排。
- 将设备、PLC、OPC UA、MQTT 遥测数据标准化后接入 MES/WMS/监控系统，或在边缘侧完成数据清洗、字段映射、校验和本地日志留存后再转发。
- 打通老旧 ERP、数据库、HTTP 接口与新系统之间的数据同步和协议转换，减少多系统之间的点对点改造。
- 用 `example/routes/**` 快速构造 POC 样例，再复制到 `lightesb-camel-app/{serviceName}/{serviceVersion}` 运行。
- 用 CLI 或管理 API 完成部署、状态检查、日志检索和自动化验证。
- 为 Codex、Claude 或其他 Agent 提供可检索的组件文档、样例和工作规则。

## 快速启动

Linux / macOS:

```bash
./start.sh
```

Windows:

```bat
start.bat
```

最小验证流程：

1. 从 `example/routes/**` 选择一个样例服务。
2. 复制完整服务目录到 `lightesb-camel-app/`。
3. 执行 `./start.sh` 或 `start.bat`。
4. 按 `example/README.md` 中的 `curl` 命令验证。
5. 演示完成后删除临时服务目录。

运行后先阅读：

- [docs/README.md](docs/README.md)：组件、CLI、API 和扩展文档索引。
- [docs/product-overview.md](docs/product-overview.md)：英文产品概览、能力矩阵、适用场景、机器人边界和网站部署口径。
- [example/README.md](example/README.md)：可复制运行的样例目录和验证命令。
- [AGENTS.md](AGENTS.md)：Agent 在本交付包内工作的规则。

## 机器人与行业集成能力

| 场景 | 支持内容 | 交付入口 |
| --- | --- | --- |
| 老系统与机器人流程接入 | HTTP/数据库/消息/企业系统接口整合，机器人任务、命令、回执、审计和外部任务流程编排 | `docs/components/01-http-route-basics.md`、`docs/cli/README.md` |
| 机器人动态技能扩展 | 轻量路由技能包、路由热加载、`server.running=false` 按需禁用、CLI 启停/部署/重载、DTS Java SPI、AI Agent + Tools、配置化协议目标和白名单 | `AGENTS.md`、`docs/cli/README.md`、`docs/extensions/01-dts-extension-guide.md`、`docs/components/12-ai-chat.md` |
| 机器人核心链路服务 | MQTT telemetry/command、边缘 AI 推理 mock 门禁、MQTT outbox dispatcher、rosbridge WebSocket JSON、ROS service/action 管理面映射、gRPC `RobotCommand` 契约草案 | `docs/robot-edge-inference-mock.md`、`docs/robot-command-dispatcher-api.md`、`docs/experience/01-robotics-protocol-precheck.md`、`proto/robot/robot_command.proto` |
| PLC 与工业现场 | OPC UA、Modbus TCP 寄存器别名、PLC4X 依赖基础和复杂 PLC 能力评估路径、AVEVA Plant SCADA | `docs/components/15-aveva-plant-scada-opcua-mqtt.md`、`docs/experience/02-robotics-protocol-correct-practices.md` |
| 数据平台与业务系统 | Kafka 风格 telemetry/event 出流、WMS/MES 外部任务接入、dashboard 数据契约、ExternalDB、SAP NetWeaver | `example/routes/RobotClusterDataSrv/v1.0.0/`、`docs/components/11-externaldb.md`、`docs/components/13-sap-netweaver.md` |

机器人、PLC 和工业现场能力默认采用 mock-first / local baseline / field validation 三层验收。交付包提供配置、路由、契约和验证入口；真实设备、broker、rosbridge、OPC UA Server、Modbus/PLC 或 Kafka 环境需要在现场提供端点、凭据、点表、ACL、测试窗口和回滚方案后进入联调。

## 轻量技能包与按需加载

LightESB 的机器人技能和协议适配能力可以以独立路由服务包交付。典型路由技能包通常是 KB 级 XML + 配置 + 少量脚本/映射文件；即使沉淀上百或上千个技能包，也不会显著增加磁盘占用。

关键机制：

- 技能包放在 `lightesb-camel-app/{serviceName}/{serviceVersion}` 目录中。
- `server.running=false` 时服务包保留在磁盘上，但默认不加载路由，不占用运行态连接和 Camel route 资源。
- 业务路由由服务包动态加载，不依赖启动时自动创建全局 CamelContext；Camel 组件能力在启用对应 XML 路由时按需解析和使用。
- 需要使用某个技能时，可通过 CLI 执行部署、启停、route reload，实现技能按需加载、按需卸载、按需恢复。
- 不需要使用时，可停止服务或保持 `server.running=false`，让平台保留技能资产但控制运行时占用。
- 适合沉淀大量机器人技能、协议适配模板、客户专用流程和现场调试能力，按任务需要启用。

路由按需加载、热更新和重启边界见 `docs/runtime-route-loading.md`。常用 CLI 入口见 `docs/cli/README.md` 和 `docs/cli/01-cli-command-reference.md`，包括 `service start/stop`、`service package deploy`、`route reload-service`、`route reload-file`、`deploy upload`、`diagnostics snapshot/warnings` 和 `robot command validate/status/submit`。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `lightesb-camel-1.0.0.jar` | LightESB-Camel 运行件 |
| `lightesb-cli.jar` | CLI 自动化工具 |
| `lightesb-camel-app/` | 正式服务运行目录，结构为 `{serviceName}/{serviceVersion}` |
| `example/routes/` | 可复制到运行目录的演示路由 |
| `example/transform-dts-java/` | DTS Java SPI 扩展示例 |
| `docs/` | 外发技术文档 |
| `skills/` | Agent 面向组件任务的技能说明 |
| `start.sh` / `start.bat` | 本地启动脚本 |

## Agent 阅读路径

Agent 处理任务时建议按以下顺序读取：

1. `AGENTS.md`
2. `docs/README.md`
3. 命中领域的 `skills/<name>/SKILL.md`
4. 相关 `docs/components/**`、`docs/cli/**`、`docs/extensions/**`
5. 对应 `example/routes/**` 样例

默认优先修改 `example/` 中的演示样例。`lightesb-camel-app/` 是正式接口运行目录，除非需要验证运行，不在其中新增索引、说明或 Agent 上下文文件。

## Support

本仓库内容可用于社区自助验证。POC 支持、实施服务、SLA 和私有化支持属于可选商业支持范围，具体边界以单独约定为准。

## License

本仓库继续使用现有 [MIT License](LICENSE)。
