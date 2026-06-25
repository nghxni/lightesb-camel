# LightESB-Camel

LightESB-Camel 是 LightESB 的可运行 Camel 交付包。LightESB 是一个轻量集成平台，面向存量系统接入，并为机器人系统提供动态热加载的技能扩展能力。

LightESB 聚焦三件事：

- 接入老系统接口和机器人自动化业务流程。
- 给机器人提供更多、更自由的动态扩展能力。
- 集成适配机器人核心能力的全链路功能服务。

本仓库不是完整源码仓库。根目录的 `lightesb-camel-1.0.0.jar`、`lightesb-cli.jar`、`start.sh` / `start.bat`、`lightesb-camel-app/`、`docs/`、`example/`、`skills/`、`AGENTS.md` 共同构成交付上下文。外部 Agent 或大模型只读取本仓库时，应优先从本 README、`AGENTS.md`、`docs/README.md` 和 `example/README.md` 建立上下文。

## 核心能力

| 能力 | 交付内容 |
| --- | --- |
| 存量系统与机器人流程接入 | Apache Camel XML 路由、Undertow HTTP 入口、老系统接口整合、机器人自动化业务流程编排 |
| 动态热加载路由技能 | 轻量路由技能包、服务目录加载、`server.running=false` 按需禁用、CLI 启停/部署/重载、DTS Java SPI 扩展、AI Agent + Tools 编排 |
| 机器人核心能力全链路服务 | MQTT telemetry/command、rosbridge/ROS 管理面、OPC UA、Modbus/PLC、Kafka 风格数据管道、gRPC 契约草案 |
| 数据转换与校验 | ConditionalTransform、JsonTransform、DataSonnet、JSON Schema 校验、DTS Java SPI 扩展 |
| 安全与治理 | IP/CIDR/Token/Regex 权限校验、全局异常响应、服务日志、H2 缓存和关键字检索 |
| 企业系统与工业协议适配 | ExternalDB 多数据源、SAP NetWeaver、AVEVA Plant SCADA、OPC UA、MQTT 5、Modbus/PLC 接入、PLC4X 评估路径 |
| 自动化运维 | LightESB CLI、部署管理 API、服务状态查询、日志查看、样例验证流程 |
| AI 集成 | AI Chat、AI Agent + Tools、面向接口编排、技能生成和运维问答的组件上下文 |

## 适用场景

- 存量 HTTP、数据库、消息、企业系统、工业协议、机器人/ROS 或第三方系统接口整合。
- 机器人自动化业务流程编排，包括任务接入、遥测标准化、命令预检、结果回执、审计和外部系统回调。
- 机器人技能或适配能力的动态扩展：通过轻量路由技能包、Camel 路由、配置文件和可选扩展组件，在不重构主系统的前提下新增能力。
- 在 Camel 路由中完成字段映射、条件转换、schema 校验、权限控制和统一错误响应。
- 面向制造、工厂自动化和机器人集成场景，承接 OPC UA、MQTT 5、Modbus/PLC、rosbridge/ROS、Kafka 风格数据出流和外部任务接入的适配、验证和交付。
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

运行后先阅读：

- [docs/README.md](docs/README.md)：组件、CLI、API 和扩展文档索引。
- [example/README.md](example/README.md)：可复制运行的样例目录和验证命令。
- [AGENTS.md](AGENTS.md)：Agent 在本交付包内工作的规则。

## 机器人与行业集成能力

| 场景 | 支持内容 | 交付入口 |
| --- | --- | --- |
| 老系统与机器人流程接入 | HTTP/数据库/消息/企业系统接口整合，机器人任务、命令、回执、审计和外部任务流程编排 | `docs/components/01-http-route-basics.md`、`docs/cli/README.md` |
| 机器人动态技能扩展 | 轻量路由技能包、路由热加载、`server.running=false` 按需禁用、CLI 启停/部署/重载、DTS Java SPI、AI Agent + Tools、配置化协议目标和白名单 | `AGENTS.md`、`docs/cli/README.md`、`docs/extensions/01-dts-extension-guide.md`、`docs/components/12-ai-chat.md` |
| 机器人核心链路服务 | MQTT telemetry/command、rosbridge WebSocket JSON、ROS service/action 管理面映射、gRPC `RobotCommand` 契约草案 | `docs/experience/01-robotics-protocol-precheck.md`、`proto/robot/robot_command.proto` |
| PLC 与工业现场 | OPC UA、Modbus TCP 寄存器别名、PLC4X 依赖基础和复杂 PLC 能力评估路径、AVEVA Plant SCADA | `docs/components/15-aveva-plant-scada-opcua-mqtt.md`、`docs/experience/02-robotics-protocol-correct-practices.md` |
| 数据平台与业务系统 | Kafka 风格 telemetry/event 出流、WMS/MES 外部任务接入、dashboard 数据契约、ExternalDB、SAP NetWeaver | `example/routes/RobotClusterDataSrv/v1.0.0/`、`docs/components/11-externaldb.md`、`docs/components/13-sap-netweaver.md` |

机器人、PLC 和工业现场能力默认采用 mock-first / local baseline / field validation 三层验收。交付包提供配置、路由、契约和验证入口；真实设备、broker、rosbridge、OPC UA Server、Modbus/PLC 或 Kafka 环境需要在现场提供端点、凭据、点表、ACL、测试窗口和回滚方案后进入联调。

## 轻量技能包与按需加载

LightESB 的机器人技能和协议适配能力可以以独立路由服务包交付。一个路由技能通常只包含 XML、配置和少量脚本/映射文件，体积很小；即使沉淀大量技能包，也不会显著增加磁盘占用。

关键机制：

- 技能包放在 `lightesb-camel-app/{serviceName}/{serviceVersion}` 目录中。
- `server.running=false` 时服务包保留在磁盘上，但默认不加载路由，不占用运行态连接和 Camel route 资源。
- 需要使用某个技能时，可通过 CLI 执行服务启动、部署或路由重载。
- 不需要使用时，可停止服务或保持 `server.running=false`，让平台保留技能资产但控制运行时占用。
- 适合沉淀大量机器人技能、协议适配模板、客户专用流程和现场调试能力，按任务需要启用。

常用 CLI 入口见 `docs/cli/README.md` 和 `docs/cli/01-cli-command-reference.md`，包括 `service start/stop`、`service package deploy`、`route reload-service`、`route reload-file` 和 `deploy upload`。

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
