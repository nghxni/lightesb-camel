# LightESB CLI 使用参考

LightESB CLI 是面向接入建模、交付运维、路由治理、日志检索和 AI 辅助编排的命令行工具。

大模型需要生成或修改 CLI 命令时，先读：

- [CLI 命令压缩参考](01-cli-command-reference.md)

核心命令域：

```text
profile -> doctor -> app -> message -> service -> service export/import/sync-remote -> deploy -> route -> log -> keyword -> ai -> diagnostics -> robot doctor -> robot list/get/capabilities/state/audit -> robot command validate/status/submit
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

- CLI 是控制面客户端，不直接修改 `lightesb-camel-app/`。
- 写操作默认传 `--yes`。
- CI 中优先用 `--output json`。
- `service import-plan` 只读远端状态；`service import` 和 `service sync-remote` 会写远端，必须加 `--yes`。
- 服务同步默认跳过远端已有同名服务版本的服务文件部署；覆盖部署需显式 `--overwrite-service-files`。
- 需要关闭部署后自动启动时加 `--no-start`；需要保留一步同步的中间导出包时加 `sync-remote --keep-package`。
- `log ask` 是可选服务端自然语言 Agent 能力，默认日志治理优先使用确定性 `log` 命令。
- `--ai-token` 只用于服务端 AI 日志问答的 `X-AI-Token`，不是模型 API key。
- `ai tool list/save/plan/run` 已删除；AI 路由生成统一走自然语言入口。
- `diagnostics snapshot/warnings` 是只读远程诊断入口，只调用 `/api/diagnostics/runtime-snapshot`，不重载路由、不清理数据、不读取远程文件；自动化和 Codex 优先使用 `--output json`。
- `keyword list/query-instances` 是只读 JSON 关键字配置和实例查询入口；`keyword add/delete` 修改关键字采集配置，必须加 `--yes`。
- `robot doctor --offline` 只做机器人接入静态检查，不连接真实机器人、broker、rosbridge、OPC UA、Modbus 或 Kafka，也不下发命令。
- `robot list/get/capabilities/state/audit` 只调用机器人管理 API 的只读入口，默认用本机 WSL mock HTTP 和本地测试验证，不证明真实资产库、真实在线状态、真实审计源或真实能力发现。
- `robot command validate --file` 只调用机器人管理 API 的 `commands:validate` 入口，不创建命令、不下发协议请求、不写执行审计。
- `robot command status --robot-id --command-id` 只查询已有命令结果，不提交新命令，不单独证明真实协议执行状态。
- `robot command submit --file --yes` 提交到服务端命令账本、审计和 MQTT outbox；`outboxStatus=pending` 只表示进入可靠派发队列，`protocolReceipt.dispatched=false` 不能当作机器人已收到或已执行。
