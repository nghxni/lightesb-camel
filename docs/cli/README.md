# LightESB CLI 使用参考

LightESB CLI 是面向接入建模、交付运维、路由治理、日志检索和 AI 辅助编排的命令行工具。

大模型需要生成或修改 CLI 命令时，先读：

- [CLI 命令压缩参考](01-cli-command-reference.md)

核心命令域：

```text
profile -> doctor -> app -> message -> service -> deploy -> route -> log -> ai -> robot doctor -> robot list/get/capabilities/state/audit -> robot command validate/status
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
- `log ask` 是可选服务端自然语言 Agent 能力，默认日志治理优先使用确定性 `log` 命令。
- `--ai-token` 只用于服务端 AI 日志问答和 AI 工具接口的 `X-AI-Token`，不是模型 API key。
- `ai tool plan/run` 只调用服务端接口，不在 CLI 本地查库或调用工具 URL；执行命令使用 `--yes`，自动化场景优先加 `--output json`。
- `robot doctor --offline` 只做机器人接入静态检查，不连接真实机器人、broker、rosbridge、OPC UA、Modbus 或 Kafka，也不下发命令。
- `robot list/get/capabilities/state/audit` 只调用机器人管理 API 的只读入口，默认用本机 WSL mock HTTP 和本地测试验证，不证明真实资产库、真实在线状态、真实审计源或真实能力发现。
- `robot command validate --file` 只调用机器人管理 API 的 `commands:validate` 入口，不创建命令、不下发协议请求、不写执行审计。
- `robot command status --robot-id --command-id` 只查询已有本地命令结果，不提交新命令，不证明真实协议执行状态。
- `robot command submit --file --yes` 只提交到本地命令持久化入口；`protocolReceipt.dispatched=false` 时不能当作真实机器人命令下发入口。
