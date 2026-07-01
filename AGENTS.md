# AGENTS.md

LightESB-Camel 交付包内 Agent 协作规则。这里是可运行交付目录，不是完整源码仓库；上下文必须自洽，不能引用、要求或假设存在未随包交付的内部架构流程文档。

## 目录边界

- `lightesb-camel-app/`：正式接口运行目录，只读参考。不要新增索引、说明或代理上下文文件。需要演示时，可以把 `example/` 中的纯演示服务复制进去运行，演示完成后删除。
- `example/`：纯演示样例目录。样例可以修改端口、服务名、接口路径和数据，用于复制到 `lightesb-camel-app/` 后临时运行。
- `docs/`：组件级技术文档，只描述可交付使用的配置、路由写法、样例和验证。
- `docs/cli/`：CLI 使用参考，只描述命令、输入、输出、确认规则和自动化边界。
- `docs/runtime-diagnostics-api.md`、`docs/robot-command-dispatcher-api.md`、`docs/*-api.md`：交付 API 与 CLI 边界说明，只写可调用契约、配置、示例和排障边界。
- `skills/`：轻量任务路由卡片。任务命中时先读对应 `skills/<name>/SKILL.md`，再读 `docs/README.md` 和组件文档。
- `services/`：第三方扩展交付物和扩展示例。

## 阅读顺序

1. 先读本文件。
2. 再读 `docs/README.md`。
3. 按任务类型读取对应 `skills/<name>/SKILL.md`。
4. 最后查阅 `docs/components/`、`docs/extensions/` 和 `example/` 中的具体样例。

## Task -> Skill 路由表

| 任务 | 先读 skill |
| --- | --- |
| 新增 HTTP 接口、编写 Camel XML、配置 `undertow`、服务目录结构 | `skills/lightesb-route-authoring/SKILL.md` |
| 配置 `conditionaltransform`、`jsontransform`、DTS 转换规则 | `skills/lightesb-transform-components/SKILL.md` |
| 配置权限校验、JSON Schema 校验、失败分支 | `skills/lightesb-security-validation/SKILL.md` |
| 配置 `servicelog`、异常兜底、H2 缓存、JsonKeyword、StreamCache | `skills/lightesb-logging-observability/SKILL.md` |
| 开发或打包第三方 DTS 扩展 | `skills/lightesb-dts-extension/SKILL.md` |
| 配置 AI Chat、SAP NetWeaver 等扩展能力 | `skills/lightesb-ai-components/SKILL.md` |
| 生成、审查或排查 CLI 命令和自动化流程 | `skills/lightesb-cli-automation/SKILL.md` |
| 运行时诊断、`diagnostics snapshot/warnings`、远程只读排障 | `skills/lightesb-cli-automation/SKILL.md`，再读 `docs/runtime-diagnostics-api.md` |
| 机器人协议样例、MQTT/rosbridge/OPC UA/Modbus/gRPC、命令 dispatcher、审计归档 | `skills/lightesb-robot-integration/SKILL.md` |
| 机器人命令 CLI 提交、validate/status、MQTT outbox 排查 | `skills/lightesb-cli-automation/SKILL.md`，再读 `skills/lightesb-robot-integration/SKILL.md` |
| 部署管理、API 响应契约、AI 路由缓存接口 | `skills/lightesb-cli-automation/SKILL.md`，再读对应 `docs/*-api.md` |

## 编写和修改规则

- 优先修改 `example/` 中的演示样例，不直接改 `lightesb-camel-app/`。
- 如确需验证运行，把 `example/` 中的完整服务目录复制到 `lightesb-camel-app/`，运行后删除临时服务目录。
- 服务目录结构保持：

```text
{ServiceName}/
  {vX.Y.Z}/
    common.config.properties
    service.config.properties
    *-route.xml
```

- `example/routes/` 中的演示服务不需要随包提供 `log4j2.properties`，程序运行时会自动生成。
- Camel XML 沿用样例现有 namespace；HTTP/转换样例多为 Spring XML schema，Timer 样例为 xml-io schema。HTTP 入站端点放在 `<from>`，处理组件放在 `<process>` 或 `<to>`。
- 不在组件文档或样例中引入未随包交付的内部材料或源码仓库开发流程。
- 外发文档不是内部完整架构文档的拷贝。只能写可交付使用的配置、路由写法、API/CLI 用法、样例、验证步骤和安全排障说明。
- 不写源码级实现路径、内部状态机细节、开发工作流、临时方案、本机路径、真实凭据或不可外发信息。
- 如需吸收内部结论，必须改写成交付视角，用组件名、配置键、命令、接口契约和示例说明。
- 外发规则文件不需要、也不应该与源码仓库内部 `AGENTS.md` 完全一致；本文件只描述随包交付目录内可执行的约束。
- 文档更新不是只改单一文件。修改组件、CLI、样例、API 或交付说明时，必须检查随包的 `docs/README.md`、对应 `docs/components/` 或 `docs/cli/`、相关 `skills/` 和 `example/` 是否需要同步。
- 如果对应文档、skill 或样例存在但不需要改，交付说明中写明原因，避免随包文档之间出现不一致。

## 可运行命令

- 启动交付包：`./start.sh`
- Windows 启动：`start.bat`
- 查看服务日志：优先查看对应服务目录下的 `logs/`。
- 验证样例：按 `docs/README.md` 或 `example/README.md` 中的 curl 示例执行。

## 验收习惯

- 文档任务：检查链接、路径、术语和样例命令。
- 路由任务：检查 XML 可读、端口不冲突、组件开关完整、日志有入口和出口。
- 配置任务：检查 `system.components`、`HTTP.Listener`、`server.port`、服务名和版本。
- 不运行破坏性命令，不清理正式接口目录。
