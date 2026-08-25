---
name: lightesb-cli-automation
description: Generate, review, or troubleshoot delivered LightESB CLI action/profile/doctor/app/message/service/deploy/route/log/keyword/ai/diagnostics/robot workflows, including sanitized errors and diagnostics.
---

# LightESB CLI 自动化

先读：

- `docs/cli/README.md`
- `docs/cli/01-cli-command-reference.md`
- `docs/cli/support-diagnostics.md`
- 诊断任务读 `docs/runtime-diagnostics-api.md`
- 机器人命令提交、dispatcher 或审计任务读 `docs/robot-command-dispatcher-api.md`
- 机器人 AI decision 查询/提交读 `docs/robot-ai-approval-api.md`
- Action 精确资格管理读 `docs/action-allowlist-api.md`
- Action 短期 token 管理读 `docs/action-token-api.md`
- Action 有界任务会话读 `docs/action-approval-api.md`
- Action 统一授权 dry-run 读 `docs/action-authorization-api.md`
- Action 安全执行读 `docs/action-execution-api.md`

规则：

- CLI 的远程命令是控制面客户端；`action validate/build` 是不使用服务端和 profile 的离线命令，`action status/list/search/get` 使用 profile bearer 查询受保护的在线快照。受控本地写还包括 `action build` 把派生索引原子写到所有服务版本目录之外；它与 `message schema generate`、显式 `ai route generate/optimize/apply --save-local` 一样必须加 `--yes`，不会自行部署或重载服务。
- `action validate --service-dir|--app-root` 输出 canonical JSON；`action build` 额外使用 `--out`。`--app-root` 模式保持严格两层契约，根级共享资源目录（如 `TransformDS`）用 `--exclude-root <目录名>`（可重复或逗号分隔）显式排除。目录契约失败按退出码 `65` 和稳定 `ACTION_*` 错误码处理，不回退到其他解析器。
- Action 在线查询要求服务端双开关和 `catalog-read`；list/search 第二页起回传第一页 revision，revision 冲突时从第一页重试。查询命令不发送 caller，不执行 Action。
- `action allowlist list/add/enable/disable` 要求服务端四开关和 `action-admin`。add 只使用 `--credential-name --action-id --service-version --yes`，enable/disable 使用 `--policy-id --yes`；不生成 caller、wildcard、block、delete 或数据库直连。
- `action token issue/introspect/revoke` 要求服务端五开关；issue 使用重复 `--action actionId@serviceVersion`、可选 TTL 和 `--yes`，revoke 使用 `--token-id --yes`。不生成 caller、credential 或 raw token 参数，原 token 只在 issue 输出一次。
- `action approval session request/get/revoke/complete` 要求六开关；request 只提交单服务版本、精确 Action/文件、输入策略摘要、副作用和有界计数。request/revoke/complete 必须 `--yes`；不生成 caller、approver、digest override、callback secret 或 approve/reject。
- 统一授权 dry-run 只提供 HTTP 诊断；不要生成虚构的 `action authorize` 命令，也不要把 dry-run decision、token 或 sessionId 当作客户端执行许可。
- `action execute` 只适配首批 `read + requestReply` Action；要求八开关、`--yes`、精确 Action/版本、二选一的输入/策略来源和独立 `lat_` 运行 token。优先从 `LIGHTESB_ACTION_TOKEN` 或 `--runtime-token-env` 指定的环境变量取 token；不发送 profile bearer，不回显 token，不生成 URI、generation、digest 或 caller 覆盖参数。
- 输入、输出或回调 JSON 校验工作流只生成 CLI 命令，不生成 Schema preview 或 AI route apply 的直接 API 调用。
- 写操作加 `--yes`，CI 中优先加 `--output json`。
- 任意命令层级都可用 `--help`；profile JSON 只使用 `tokenConfigured`、`aiTokenConfigured` 状态，不读取或记录 token 值。
- 需要服务端地址时优先使用 `--server` 或 profile，不在命令中写真实密钥。
- `--ai-token` 只用于 `X-AI-Token`，不是模型 API key。
- `ai tool list/save/plan/run` 已删除；AI 路由生成统一走自然语言入口。
- `keyword list/query-instances` 只读；`keyword add/delete` 修改 JsonKeyword keyName 配置，必须加 `--yes`。
- JSON 校验路由已有消息模型时，先用 `service list/get --output json` 解析服务关系：INPUT 取当前 `serviceInId`，OUTPUT 取当前 `serviceOutId`，CALLBACK 先用 `serviceCallbackId` 查询回调服务再取其 `serviceInId`。
- 按方向执行 `message schema generate --id|--file --service-name --service-version --schema-file request-schema.json|response-schema.json|callback-schema.json --yes --output json`，只使用返回的 `schema` 和服务版本目录相对 `jsonSchemaPath`；`file` 仅表示实际写盘位置，不要手写或由模型补齐 Schema。
- `warnings` 非空时停止自动 apply 并展示完整 warnings，只有用户明确确认后继续。用户明确授权远程写入时，才用 `ai route apply --save-remote --yes` 一次提交实际 route 文件名、两个 properties 和 route 引用的固定 Schema；普通本地直接编辑服务文件不以 CLI apply 为前置。
- `ai route apply --resource-file` 只写不含目录的文件名时，相对 `--file` 指定的 route XML 所在目录解析；绝对路径和包含目录的相对路径保持按原路径解析。JSON 资源只接受三个固定 Schema `.json`；删除校验块时不提交对应 Schema，服务端会删除受管文件。`FAILED`、`FAILED_ROLLED_BACK`、`ROLLBACK_FAILED` 都按失败处理，先读取 operationId 和恢复诊断，不自动重试。
- 会话受管 route apply 使用成对 `--action-session-id --expected-scope-digest`，只允许远程保存、不允许日志选项。digest 取最新 session JSON；STALE/冲突/恢复失败停止，不回退普通 apply。sessionId 不是执行许可。
- `service import-plan` 只读远端状态；`service package build`、`service export/import/sync-remote` 和 `deploy upload` 必须加 `--yes`。
- `deploy upload` 不接受 `--target-directory`；部署目标由服务端运行配置统一决定。
- `route reload-file/unload --file-path` 必须指向服务端受管路由根内真实 XML 文件；
  `route config` 只返回相对服务目录和脱敏配置，不得期待服务器绝对路径或敏感值。
- CLI HTTP 错误和 diagnostics 摘要始终脱敏，不随服务日志开关或用户角色返回原文；服务级开关关闭只意味着服务/实例持久化可能包含原文。
- 服务同步默认跳过远端已有同名服务版本的服务文件部署；覆盖部署需显式 `--overwrite-service-files`。
- 服务同步默认自动启动部署路由；需要关闭时使用 `--no-start`。`sync-remote --keep-package` 可保留中间导出包。
- `service start/stop` 会等待真实 Camel 上下文状态；HTTP 409 时先查询服务状态或运行时诊断，超时不会回滚 `server.running`，不要立即发送反向请求覆盖目标。
- 服务同步中远端已有同名报文且内容不一致时走消息更新接口，要求远端当前版本为 `V数字.单数字`，更新后递增单数字小版本并保留历史；小版本为 `9` 时进位，例如 `V1.9` -> `V2.0`。
- `robot doctor --offline` 只做本地静态检查，不连接真实 endpoint，不下发机器人命令。
- `robot doctor --runtime` 只调用 `/api/diagnostics/runtime-snapshot?component=robot-command`，检查表、outbox、状态快照、补偿、denylist 和最近错误码分布；保持 `connectivityChecked=false`，不连接真实 endpoint、不调用验证 route。
- `robot list/get/capabilities/state/audit` 只做机器人管理 API 只读查询，不证明真实资产库、真实在线状态、真实审计源或真实能力发现。
- `robot command validate --file` 只调用 `POST /service-management/v1/robots/{robotId}/commands:validate`，不调用 `/commands`，不创建命令或执行审计。
- `robot command status --robot-id --command-id` 只调用 `GET /service-management/v1/robots/{robotId}/commands/{commandId}`，不提交新命令或连接真实协议 endpoint。
- `robot command submit --file --yes` 只调用 `POST /service-management/v1/robots/{robotId}/commands` 命令账本、审计和 MQTT outbox 入口；`protocolReceipt.dispatched=false` 时不能当作真实协议执行成功。
- `robot inference decision-status` 只查询脱敏 decision；`robot inference submit --yes` 只发送 opaque decision ID 和空对象。不生成 approve/reject 命令，不读候选命令文件，不保存 HMAC secret。
- `robot command ingest-receipt --receipt-type ack|result --topic --payload-file|--payload-json --yes` 只调用 `POST /service-management/v1/robots/mqtt-receipts:ingest`，不订阅 MQTT、不直连 broker、不自动 submit/dispatch 命令。
- `robot policy list/add/enable/disable` 只调用机器人管理 API denylist；`add`、`enable` 和 `disable` 必须带 `--yes`，不直连数据库、不连接真实机器人、不触发协议调用。
- 机器人 CLI 后续真实执行能力必须另开协议闭环切片；不要生成协议写控命令。
- 机器人 CLI 默认只要求本机 WSL 可运行 Maven；用 mock HTTP 和本地测试验证，不要求真实地址或真实机器人环境。
- AI 路由生成和优化只返回候选内容，不自动保存、打包或部署。
- 排查部署问题时先查 `deploy status/history`、`route status/mapping`、`log instance`。
- 售后诊断先按问题类型选择只读命令，优先 `--output json`，记录服务名/版本、fileKey/routeId、requestId/traceId/exchangeId、CLI 输出摘要和恢复动作。
- 售后输出不得包含完整 prompt、完整模型响应、完整 payload、完整 XML/properties、连接串、本地绝对路径或客户敏感数据。

常用链路：

```bash
lightesb action validate --service-dir lightesb-camel-app/DemoSrv/v1.0.0
lightesb action build --app-root lightesb-camel-app --out build/action-index.json --yes
lightesb action status
lightesb action list --page-num 1 --page-size 20
lightesb action search --query security --page-num 1 --page-size 20
lightesb action get --action-id demo-security-check --service-version v1.0.0 --output json
lightesb action allowlist list --limit 50 --output json
lightesb action allowlist add --credential-name agent-executor --action-id payment.lookup --service-version v1 --yes --output json
lightesb action token issue --action payment.lookup@v1 --ttl-seconds 300 --yes --output json
lightesb action token introspect --token-id <tokenId> --output json
lightesb action token revoke --token-id <tokenId> --yes --output json
lightesb action approval session get --session-id <sessionId> --output json
lightesb ai route apply --server http://localhost:8080 --file DemoSrv-route.xml --service-name DemoSrv --service-version v1.0.0 --route-file-name DemoSrv-route.xml --resource-file common.config.properties --resource-file service.config.properties --save-remote --action-session-id <sessionId> --expected-scope-digest <currentScopeDigest> --yes --output json
lightesb profile add --name dev --server http://localhost:8080
lightesb profile use dev
lightesb doctor
lightesb app create --file app.json --yes
lightesb message create --file request-message.json --yes
lightesb message create --file response-message.json --yes
lightesb message schema generate --server http://localhost:8080 --id <messageId> --service-name DemoSrv --service-version v1.0.0 --schema-file request-schema.json --yes --output json
lightesb ai route apply --server http://localhost:8080 --file DemoSrv-route.xml --service-name DemoSrv --service-version v1.0.0 --route-file-name DemoSrv-route.xml --resource-file common.config.properties --resource-file service.config.properties --resource-file request-schema.json --save-remote --return-logs --yes --output json
lightesb service create --file service.json --yes
lightesb service config save --file service.json --yes
lightesb service package build --file package.json --yes
lightesb service package deploy --file package.json --yes
lightesb service export --local-server http://localhost:8080 --app-dir lightesb-camel-app --service-name DemoSrv --service-version v1.0.0 --out dist/DemoSrv-v1.0.0.lightesb-service.zip --yes
lightesb service import-plan --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip
lightesb service import --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip --skip-existing --yes
lightesb service start --id <serviceId> --yes --output json
lightesb service stop --id <serviceId> --yes --output json
lightesb deploy upload ./DemoSrv.zip --yes
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
lightesb robot inference decision-status --server http://localhost:8080 --robot-id quad-001 --decision-id "$DECISION_ID" --output json
lightesb robot inference submit --server http://localhost:8080 --robot-id quad-001 --decision-id "$DECISION_ID" --yes --output json
lightesb robot command ingest-receipt --server http://localhost:8080 --receipt-type ack --topic robot/site-a/quad-001/command/cmd-001/ack --payload-file ack.json --yes --output json
lightesb robot policy list --server http://localhost:8080 --output json
```

`service start/stop` 最长会等待 130 秒以接收服务端转换结果；CI 或外层脚本不要设置短于该值的命令超时，否则可能丢失结构化 `409` 和诊断详情。

验收：

- 命令能说明输入文件、服务端地址和是否写操作。
- 写操作有 `--yes` 或明确说明需要人工确认。
- 输出给 CI 的命令使用 `--output json`。
- AI 相关说明不要求本地保存模型 provider 密钥。
- JSON Schema 自动流程能证明消息 ID 来源、固定文件映射和 warnings 人工门禁，不自行生成 Schema。
- 售后诊断证据已脱敏，且不会把只读采证误写成 reload、deploy、cleanup 或日志级别调整。
