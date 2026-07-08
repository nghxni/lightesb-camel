---
name: lightesb-cli-automation
description: 生成、审查或排查 LightESB CLI 命令、profile、doctor、app/message/service/deploy/route/log/keyword/ai/diagnostics/robot 自动化流程时使用。
---

# LightESB CLI 自动化

先读：

- `docs/cli/README.md`
- `docs/cli/01-cli-command-reference.md`
- `docs/cli/support-diagnostics.md`
- 诊断任务读 `docs/runtime-diagnostics-api.md`
- 机器人命令提交、dispatcher 或审计任务读 `docs/robot-command-dispatcher-api.md`

规则：

- CLI 是控制面客户端，不直接修改 `lightesb-camel-app/`。
- 写操作加 `--yes`，CI 中优先加 `--output json`。
- 需要服务端地址时优先使用 `--server` 或 profile，不在命令中写真实密钥。
- `--ai-token` 只用于 `X-AI-Token`，不是模型 API key。
- `ai tool list/save/plan/run` 已删除；AI 路由生成统一走自然语言入口。
- `keyword list/query-instances` 只读；`keyword add/delete` 修改 JsonKeyword keyName 配置，必须加 `--yes`。
- `service import-plan` 只读远端状态；`service import` 和 `service sync-remote` 必须加 `--yes`。
- 服务同步默认跳过远端已有同名服务版本的服务文件部署；覆盖部署需显式 `--overwrite-service-files`。
- 服务同步默认自动启动部署路由；需要关闭时使用 `--no-start`。`sync-remote --keep-package` 可保留中间导出包。
- 服务同步中远端已有同名报文且内容不一致时走消息更新接口，要求远端当前版本为 `V数字.单数字`，更新后递增单数字小版本并保留历史；小版本为 `9` 时进位，例如 `V1.9` -> `V2.0`。
- `robot doctor --offline` 只做本地静态检查，不连接真实 endpoint，不下发机器人命令。
- `robot doctor --runtime` 只调用 `/api/diagnostics/runtime-snapshot?component=robot-command`，检查表、outbox、状态快照、补偿、denylist 和最近错误码分布；保持 `connectivityChecked=false`，不连接真实 endpoint、不调用验证 route。
- `robot list/get/capabilities/state/audit` 只做机器人管理 API 只读查询，不证明真实资产库、真实在线状态、真实审计源或真实能力发现。
- `robot command validate --file` 只调用 `POST /service-management/v1/robots/{robotId}/commands:validate`，不调用 `/commands`，不创建命令或执行审计。
- `robot command status --robot-id --command-id` 只调用 `GET /service-management/v1/robots/{robotId}/commands/{commandId}`，不提交新命令或连接真实协议 endpoint。
- `robot command submit --file --yes` 只调用 `POST /service-management/v1/robots/{robotId}/commands` 命令账本、审计和 MQTT outbox 入口；`protocolReceipt.dispatched=false` 时不能当作真实协议执行成功。
- `robot command ingest-receipt --receipt-type ack|result --topic --payload-file|--payload-json --yes` 只调用 `POST /service-management/v1/robots/mqtt-receipts:ingest`，不订阅 MQTT、不直连 broker、不自动 submit/dispatch 命令。
- `robot policy list/add/disable` 只调用机器人管理 API denylist；`add` 和 `disable` 必须带 `--yes`，不直连数据库、不连接真实机器人、不触发协议调用。
- 机器人 CLI 后续真实执行能力必须另开协议闭环切片；不要生成协议写控命令。
- 机器人 CLI 默认只要求本机 WSL 可运行 Maven；用 mock HTTP 和本地测试验证，不要求真实地址或真实机器人环境。
- AI 路由生成和优化只返回候选内容，不自动保存、打包或部署。
- 排查部署问题时先查 `deploy status/history`、`route status/mapping`、`log instance`。
- 售后诊断先按问题类型选择只读命令，优先 `--output json`，记录服务名/版本、fileKey/routeId、requestId/traceId/exchangeId、CLI 输出摘要和恢复动作。
- 售后输出不得包含完整 prompt、完整模型响应、完整 payload、完整 XML/properties、连接串、本地绝对路径或客户敏感数据。

常用链路：

```bash
lightesb profile add --name dev --server http://localhost:8080
lightesb profile use dev
lightesb doctor
lightesb app create --file app.json --yes
lightesb message create --file request-message.json --yes
lightesb message create --file response-message.json --yes
lightesb service create --file service.json --yes
lightesb service config save --file service.json --yes
lightesb service package deploy --file package.json --yes
lightesb service export --local-server http://localhost:8080 --app-dir lightesb-camel-app --service-name DemoSrv --service-version v1.0.0 --out dist/DemoSrv-v1.0.0.lightesb-service.zip
lightesb service import-plan --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip
lightesb service import --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip --skip-existing --yes
lightesb route status
lightesb log instance list --service-name DemoSrv --service-version 1.0.0
lightesb keyword list --service-name DemoSrv --service-version 1.0.0 --output json
lightesb keyword add --service-name DemoSrv --service-version 1.0.0 --key-name patientId --yes
lightesb keyword query-instances --service-name DemoSrv --service-version 1.0.0 --key-name patientId --json-value 10001 --output json
lightesb diagnostics snapshot --server http://localhost:8080 --output json
lightesb diagnostics warnings --server http://localhost:8080 --output json
lightesb diagnostics snapshot --server http://localhost:8080 --service-name DemoSrv --service-version v1.0.0 --component route-runtime --output json
lightesb robot doctor --server http://localhost:8080 --runtime --output json
lightesb robot command validate --server http://localhost:8080 --file robot-command.json --output json
lightesb robot command submit --server http://localhost:8080 --file robot-command.json --yes --output json
lightesb robot command ingest-receipt --server http://localhost:8080 --receipt-type ack --topic robot/site-a/quad-001/command/cmd-001/ack --payload-file ack.json --yes --output json
lightesb robot policy list --server http://localhost:8080 --output json
```

验收：

- 命令能说明输入文件、服务端地址和是否写操作。
- 写操作有 `--yes` 或明确说明需要人工确认。
- 输出给 CI 的命令使用 `--output json`。
- AI 相关说明不要求本地保存模型 provider 密钥。
- 售后诊断证据已脱敏，且不会把只读采证误写成 reload、deploy、cleanup 或日志级别调整。
