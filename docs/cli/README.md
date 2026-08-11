# LightESB CLI 使用参考

LightESB CLI 是面向接入建模、交付运维、路由治理、日志检索和 AI 辅助编排的命令行工具。

大模型需要生成或修改 CLI 命令时，先读：

- [CLI 命令压缩参考](01-cli-command-reference.md)
- [Support Diagnostics](support-diagnostics.md)

核心命令域：

```text
action validate/build -> profile -> action status/list/search/get -> action allowlist list/add/enable/disable -> doctor -> app -> message -> message schema generate -> service -> service export/import/sync-remote -> deploy -> route -> log -> keyword -> ai -> diagnostics -> robot doctor --offline/--runtime -> robot list/get/capabilities/state/audit -> robot command validate/status/submit/ingest-receipt -> robot inference decision-status/submit
```

基本调用：

```bash
lightesb --server http://localhost:8080 <command>
lightesb --profile dev <command>
lightesb --output json <command>
lightesb --yes <write-command>
lightesb --file payload.json <command>
```

安全边界：

- CLI 的远程命令是控制面客户端；`action validate/build` 是纯离线命令，`action status/list/search/get` 使用 profile bearer 读取在线快照。受控本地写还包括 `action build` 把派生索引原子写到所有服务版本目录之外；它与 `message schema generate`、显式 `ai route generate/optimize/apply --save-local` 一样必须加 `--yes`，不会自行部署或重载服务。
- `action validate --service-dir|--app-root` 输出 canonical JSON；`action build` 额外使用 `--out`。在线分页第二页起回传第一页 revision，冲突时从第一页重试。全部 Action 命令均不执行 Action；离线契约失败返回退出码 `65` 和稳定 `ACTION_*` 错误码。
- `action allowlist list/add/enable/disable` 管理精确资格；add 只使用服务端 credential name，写操作要求 `--yes`。不得提供 caller、wildcard、block、delete 或数据库直连。
- 写操作默认传 `--yes`。
- CI 中优先用 `--output json`。
- 任意命令层级都支持 `--help`；profile JSON 只返回 `tokenConfigured`、`aiTokenConfigured` 状态，不输出 token 值。
- `service import-plan` 只读远端状态；`service package build`、`service export/import/sync-remote` 和 `deploy upload` 是写操作，必须加 `--yes`。
- 服务同步默认跳过远端已有同名服务版本的服务文件部署；覆盖部署需显式 `--overwrite-service-files`。
- 需要关闭部署后自动启动时加 `--no-start`；需要保留一步同步的中间导出包时加 `sync-remote --keep-package`。
- `log ask` 是可选服务端自然语言 Agent 能力，默认日志治理优先使用确定性 `log` 命令。
- `--ai-token` 只用于服务端 AI 日志问答的 `X-AI-Token`，不是模型 API key。
- `ai tool list/save/plan/run` 已删除；AI 路由生成统一走自然语言入口。
- `diagnostics snapshot/warnings` 是只读远程诊断入口，只调用 `/api/diagnostics/runtime-snapshot`，不重载路由、不清理数据、不读取远程文件；自动化和 Codex 优先使用 `--output json`。
- `keyword list/query-instances` 是只读 JSON 关键字配置和实例查询入口；`keyword add/delete` 修改关键字采集配置，必须加 `--yes`。
- `message schema generate` 使用 `--id` 或 `--file` 调用消息 Schema 预览接口，并写入显式服务版本目录；JSON 输出中的 `jsonSchemaPath` 可直接用于路由 `JsonSchemaPath`。
- 输入、输出或回调 JSON 校验先通过 `service list/get --output json` 确定消息 ID，再生成 `request-schema.json`、`response-schema.json` 或 `callback-schema.json`。Schema 内容只取服务端响应；`warnings` 非空时停止自动 apply，只有用户明确确认后才能继续。
- 用户明确授权远程写入时，用 `ai route apply --save-remote --yes` 一次提交实际 route 文件名、两个 properties 和 route 引用的固定 Schema。普通本地直接编辑服务文件不以 CLI apply 为前置。`FAILED_ROLLED_BACK` 或 `ROLLBACK_FAILED` 时保留本地候选，按 operationId 和恢复诊断排查，不自动重试覆盖。
- `robot doctor --offline` 只做机器人接入静态检查，不连接真实机器人、broker、rosbridge、OPC UA、Modbus 或 Kafka，也不下发命令。
- `robot doctor --runtime` 只调用 `/api/diagnostics/runtime-snapshot?component=robot-command`，检查表、outbox、状态快照、补偿、denylist 和最近错误码分布；输出 `connectivityChecked=false`，不连接真实机器人、不调用验证 route。
- `robot list/get/capabilities/state/audit` 只调用机器人管理 API 的只读入口。`robot state` 文本输出包含 `onlineStatus`、`protocolProfile`、`lastCommandId`、`lastErrorCode`、`sourceType` 和 `updatedAt`；批量状态快照和补偿积压分页查询当前直接使用管理 API `GET /service-management/v1/robots/state-snapshots`、`GET /service-management/v1/robots/compensations`，不新增 CLI 命令。默认用本机 WSL mock HTTP 和本地测试验证，不证明真实资产库、真实在线状态、真实审计源或真实能力发现。
- `robot command validate --file` 只调用机器人管理 API 的 `commands:validate` 入口，不创建命令、不下发协议请求、不写执行审计。
- `robot command status --robot-id --command-id` 只查询已有命令结果，不提交新命令，不单独证明真实协议执行状态。
- `robot command submit --file --yes` 提交到服务端命令账本、审计和 MQTT outbox；`outboxStatus=pending` 只表示进入可靠派发队列，`protocolReceipt.dispatched=false` 不能当作机器人已收到或已执行。
- `robot inference decision-status --robot-id --decision-id` 只查询脱敏 decision；`robot inference submit --robot-id --decision-id --yes` 只发送空对象并消费已验签批准的 decision。CLI 不提供 approve/reject，不读候选命令文件，不保存 HMAC secret。
- `robot command ingest-receipt --receipt-type ack|result --topic --payload-file|--payload-json --yes` 只调用服务端 MQTT 回执 ingest 入口；不订阅 MQTT、不直连 broker、不自动 submit/dispatch 命令。
- `robot policy list|add|enable|disable` 只调用机器人管理 API 的 denylist 入口。`add`、`enable` 和 `disable` 必须加 `--yes`；不直连数据库、不连接真实机器人、不触发协议调用。
