# 机器人 AI 可信审批与一次性提交

## 验收步骤

1. 默认不配置 `lightesb.robot.ai.approval.enabled`，确认审批回调、decision 查询和 AI submit API 均不注册。
2. 开启时同时配置全局 HMAC provider 和服务路由的 approval 开关。
3. 使用原始 JSON 字节计算签名，发送 approval callback，确认 decision 由 `pending` 转为 `approved` 或 `rejected`。
4. 用 GET 查询脱敏 decision；用带 `--yes` 的 CLI 或空请求体 API 提交已批准 decision。
5. 验证重放 event、过期 decision、普通 `/commands` 绕过和二次消费都 fail closed，不产生第二条 outbox。

## 显式配置

该能力默认关闭。关闭时不要在配置文件写 `enabled=false`；只在启用时写完整配置：

```properties
lightesb.robot.ai.approval.enabled=true
lightesb.robot.ai.approval.provider=hmac-webhook
lightesb.robot.ai.approval.hmac.provider-name=site-approval
lightesb.robot.ai.approval.hmac.key-id=site-approval-v1
lightesb.robot.ai.approval.hmac.secret=${ROBOT_AI_APPROVAL_HMAC_SECRET}
lightesb.robot.ai.approval.hmac.allowed-approver-ids=operator-001,operator-002
lightesb.robot.ai.approval.hmac.max-clock-skew-seconds=60
lightesb.robot.ai.approval.hmac.max-body-bytes=65536
lightesb.robot.ai.approval.decision-max-age-ms=60000
```

密钥必须通过环境变量或启动参数注入，不得写入仓库、日志、响应或审计。服务路由还必须显式设置：

```properties
robot.ai.inference.enabled=true
robot.ai.inference.approval.enabled=true
```

decision 有效期是推理 freshness、候选命令 TTL 和 `decision-max-age-ms` 三者的最小值；审批不能延长任何上游时效。

## HMAC 审批回调

```text
POST /service-management/v1/robots/ai/approval-events
```

必填 header：

| Header | 说明 |
| --- | --- |
| `X-LightESB-Approval-Key-Id` | 服务端配置的 key ID。 |
| `X-LightESB-Approval-Timestamp` | UTC epoch seconds，必须在时钟偏差窗口内。 |
| `X-LightESB-Approval-Event-Id` | provider 事件幂等键，与 body `eventId` 一致。 |
| `X-LightESB-Approval-Signature` | `v1=` 加小写十六进制 HMAC-SHA256。 |

请求体：

```json
{
  "eventId": "approval-event-001",
  "providerDecisionId": "provider-task-1001",
  "validationDecisionId": "vaid_0123456789abcdef0123456789abcdef",
  "candidateDigest": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "status": "approved",
  "approverId": "operator-001",
  "occurredAt": "2026-07-22T12:00:10Z"
}
```

`status` 只允许 `approved` 或 `rejected`。签名覆盖请求实际发送的 raw body，不对 JSON 重排。签名串使用 UTF-8，用单个 LF 连接，末尾无额外 LF：

```text
v1
POST
/service-management/v1/robots/ai/approval-events
<epoch-seconds>
<event-id>
<lowercase-hex-sha256-of-raw-body>
```

签名值为：

```text
v1=<lowercase-hex-HMAC-SHA256(secret, signing-string)>
```

```bash
curl -X POST http://localhost:8080/service-management/v1/robots/ai/approval-events \
  -H 'Content-Type: application/json' \
  -H 'X-LightESB-Approval-Key-Id: site-approval-v1' \
  -H "X-LightESB-Approval-Timestamp: ${TIMESTAMP}" \
  -H 'X-LightESB-Approval-Event-Id: approval-event-001' \
  -H "X-LightESB-Approval-Signature: ${SIGNATURE}" \
  --data-binary @approval-event.json
```

成功响应：

```json
{
  "success": true,
  "data": {
    "eventId": "approval-event-001",
    "validationDecisionId": "vaid_0123456789abcdef0123456789abcdef",
    "status": "approved",
    "provider": "site-approval",
    "providerDecisionId": "provider-task-1001",
    "approverId": "operator-001",
    "occurredAt": "2026-07-22T12:00:10Z",
    "expiresAt": "2026-07-22T12:00:30Z",
    "duplicate": false
  },
  "error": null,
  "requestId": "REQ-AI-APPROVAL"
}
```

同 provider/event ID 与完全相同 raw body 的重试返回幂等结果；同 ID 异内容返回 `409 ROBOT_AI_APPROVAL_REPLAY_CONFLICT`。

## Decision 查询

```text
GET /service-management/v1/robots/{robotId}/ai-validation-decisions/{validationDecisionId}
```

路径参数 `robotId` 必须与 decision 绑定一致；`validationDecisionId` 是 LightESB 生成的 `vaid_` 加 32 位小写十六进制 opaque ID。

```bash
curl http://localhost:8080/service-management/v1/robots/quad-001/ai-validation-decisions/vaid_0123456789abcdef0123456789abcdef
```

```json
{
  "success": true,
  "data": {
    "validationDecisionId": "vaid_0123456789abcdef0123456789abcdef",
    "inferenceId": "inf-001",
    "robotId": "quad-001",
    "siteId": "site-a",
    "commandId": "cmd-ai-001",
    "commandType": "move_to",
    "riskLevel": "medium",
    "persistedStatus": "approved",
    "effectiveStatus": "approved",
    "approvalProvider": "site-approval",
    "approverId": "operator-001",
    "expiresAt": "2026-07-22T12:00:30Z",
    "consumedAt": null,
    "boundCommandId": null
  },
  "error": null,
  "requestId": "REQ-AI-STATUS"
}
```

响应 `data` 包含 decision/inference/robot/site/command ID、candidate digest、命令类型、模型/策略/风险摘要、`persistedStatus`、`effectiveStatus`、provider/approver 摘要、时间和绑定 command ID。不返回候选命令 JSON、审批正文、raw callback、signature 或 secret。

若 pending/approved decision 已超过 `expiresAt`，GET 返回 `effectiveStatus=expired`，但不修改数据库。callback 或 submit 才在事务内推进持久化状态。

## 一次性 AI Submit

```text
POST /service-management/v1/robots/{robotId}/ai-validation-decisions/{validationDecisionId}:submit
```

请求体省略或为 `{}`。服务端从持久化 decision 还原候选命令，重验 candidate digest、denylist、capability 和当前安全策略，并在同一事务写 command、audit、outbox、state snapshot 和 `consumed` 绑定。任一步失败全部回滚。

```bash
curl -X POST \
  http://localhost:8080/service-management/v1/robots/quad-001/ai-validation-decisions/vaid_0123456789abcdef0123456789abcdef:submit \
  -H 'Content-Type: application/json' \
  -d '{}'
```

```json
{
  "success": true,
  "data": {
    "commandId": "cmd-ai-001",
    "robotId": "quad-001",
    "status": "accepted",
    "protocolReceipt": {
      "dispatched": false,
      "outboxStatus": "pending"
    }
  },
  "error": null,
  "requestId": "REQ-AI-SUBMIT"
}
```

`accepted/outboxStatus=pending` 只表示命令进入可靠派发队列，不表示机器人已收到或执行。普通 `/commands` 遇到 AI decision 已保留的 `robotId + commandId` 返回 `422 ROBOT_AI_APPROVAL_REQUIRED`。

## CLI

```bash
lightesb robot inference decision-status \
  --robot-id quad-001 \
  --decision-id vaid_0123456789abcdef0123456789abcdef \
  --output json

lightesb robot inference submit \
  --robot-id quad-001 \
  --decision-id vaid_0123456789abcdef0123456789abcdef \
  --yes --output json
```

CLI 不提供 approve/reject，不读取候选命令文件，不保存 HMAC secret。

## 错误码

| HTTP | code | 场景 |
| ---: | --- | --- |
| 400 | `ROBOT_AI_APPROVAL_EVENT_INVALID` / `ROBOT_AI_SUBMIT_INVALID` | 回调契约或 submit 输入非法。 |
| 401 | `ROBOT_AI_APPROVAL_SIGNATURE_INVALID` | key ID、timestamp 或签名无效。 |
| 404 | `ROBOT_AI_VALIDATION_DECISION_NOT_FOUND` | decision 不存在或 robot 不匹配。 |
| 409 | `ROBOT_AI_APPROVAL_REPLAY_CONFLICT` / `ROBOT_AI_APPROVAL_STATE_CONFLICT` | event 重放冲突或终态改写。 |
| 409 | `ROBOT_AI_DECISION_CONSUMPTION_CONFLICT` | consumed decision 与 command/outbox 绑定不一致。 |
| 422 | `ROBOT_AI_APPROVER_NOT_ALLOWED` | approver 不在服务端 allowlist。 |
| 422 | `ROBOT_AI_APPROVAL_REQUIRED` | 未批准、已拒绝或普通入口绕过。 |
| 422 | `ROBOT_AI_VALIDATION_DECISION_EXPIRED` | decision 已过期。 |
| 422 | `ROBOT_AI_CANDIDATE_DIGEST_MISMATCH` | 候选、审批或身份绑定不一致。 |
| 503 | `ROBOT_AI_DECISION_STORE_UNAVAILABLE` | decision 存储或事务不可用。 |

## MySQL 与 H2 边界

生产 MySQL 8 使用 `docs/sql/robot-ai-approval-mysql.sql` 预建两张表和索引。H2 fallback 只用于小数据量 POC，不代表生产级并发、备份恢复或迁移能力。交付环境仍应验证 MySQL DDL 权限、唯一键冲突、行锁、事务回滚和索引元数据。
