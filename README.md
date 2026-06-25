# LightESB-Camel

LightESB-Camel 是 LightESB 的可运行 Camel 交付包，用于在不重构存量系统的前提下完成接口整合、协议适配、数据转换、运行时治理和 AI 辅助编排。

本仓库不是完整源码仓库。根目录的 `lightesb-camel-1.0.0.jar`、`lightesb-cli.jar`、`start.sh` / `start.bat`、`lightesb-camel-app/`、`docs/`、`example/`、`skills/`、`AGENTS.md` 共同构成交付上下文。外部 Agent 或大模型只读取本仓库时，应优先从本 README、`AGENTS.md`、`docs/README.md` 和 `example/README.md` 建立上下文。

## 核心能力

| 能力 | 交付内容 |
| --- | --- |
| HTTP 接口与路由编排 | Apache Camel XML 路由、Undertow HTTP 入口、服务目录加载、路由热加载 |
| 数据转换与校验 | ConditionalTransform、JsonTransform、DataSonnet、JSON Schema 校验、DTS Java SPI 扩展 |
| 安全与治理 | IP/CIDR/Token/Regex 权限校验、全局异常响应、服务日志、H2 缓存和关键字检索 |
| 数据访问与协议适配 | ExternalDB、多数据源、SAP NetWeaver、AVEVA Plant SCADA OPC UA / MQTT、机器人协议样例 |
| 自动化运维 | LightESB CLI、部署管理 API、服务状态查询、日志查看、样例验证流程 |
| AI 集成 | AI Chat、AI Agent + Tools 样例、面向接口编排和运维问答的组件上下文 |

## 适用场景

- 存量 HTTP、数据库、消息、工业协议或第三方系统接口整合。
- 在 Camel 路由中完成字段映射、条件转换、schema 校验、权限控制和统一错误响应。
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
