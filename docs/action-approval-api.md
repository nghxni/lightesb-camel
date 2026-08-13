# Action 有界任务会话审批

## 启用

该能力默认关闭。现场必须同时显式开启 catalog、security、audit、allowlist、token 和 approval，并配置 HMAC provider：

```properties
lightesb.action-catalog.enabled=true
lightesb.action-security.enabled=true
lightesb.action-audit.enabled=true
lightesb.action-allowlist.enabled=true
lightesb.action-token.enabled=true
lightesb.action-approval.enabled=true

lightesb.action-approval.hmac.provider-name=${LIGHTESB_APPROVAL_PROVIDER:}
lightesb.action-approval.hmac.key-id=${LIGHTESB_APPROVAL_KEY_ID:}
lightesb.action-approval.hmac.secret=${LIGHTESB_APPROVAL_HMAC_SECRET:}
lightesb.action-approval.hmac.allowed-approver-ids[0]=${LIGHTESB_APPROVER_ID:}
```

HMAC secret 至少 32 字符，只通过 secret manager 或环境变量注入。会话不是 bearer 或 Action 执行许可；它只记录人工批准的有界任务范围和受管 route 变更来源。真实执行仍由服务端重新终检并消费一次性许可，见 `action-execution-api.md`。

## CLI 流程

1. 使用 `action-execute` profile 请求会话：

```bash
lightesb action approval session request \
  --service-name OrderSrv \
  --service-version v1.0.0 \
  --action-id order-check \
  --allowed-file OrderSrv-route.xml \
  --allowed-file common.config.properties \
  --allowed-file service.config.properties \
  --input-policy-digest '<sha256>' \
  --side-effect-ceiling write \
  --ttl-seconds 900 \
  --max-transitions 5 \
  --max-executions 10 \
  --yes --output json
```

2. 外部审批 provider 调用 callback 批准或拒绝。CLI 不提供本地 approve/reject，也不保存 HMAC secret。

3. 查询最新状态和 `currentScopeDigest`：

```bash
lightesb action approval session get --session-id '<sessionId>' --output json
```

4. 批准后，用同一会话受管应用 route：

```bash
lightesb ai route apply --file OrderSrv-route.xml \
  --save-remote \
  --service-name OrderSrv \
  --service-version v1.0.0 \
  --route-file-name OrderSrv-route.xml \
  --resource-file common.config.properties \
  --resource-file service.config.properties \
  --action-session-id '<sessionId>' \
  --expected-scope-digest '<currentScopeDigest>' \
  --yes --output json
```

会话参数必须成对使用，只能远程保存，不能组合 `--return-logs` 或 `--log-lines`。普通 `ai route apply` 仍可使用，但不会获得会话 digest lineage。

5. 任务结束后完成或撤销：

```bash
lightesb action approval session complete --session-id '<sessionId>' --yes
lightesb action approval session revoke --session-id '<sessionId>' --yes
```

## API

| Method | Endpoint | 说明 |
| --- | --- | --- |
| POST | `/api/actions/approval/sessions` | 为 bearer 派生的 caller 请求会话。 |
| GET | `/api/actions/approval/sessions/{sessionId}` | 查询并重验当前会话。 |
| POST | `/api/actions/approval/sessions/{sessionId}:revoke` | 撤销会话。 |
| POST | `/api/actions/approval/sessions/{sessionId}:complete` | 主动完成会话。 |
| POST | `/api/actions/approval/sessions/{sessionId}:apply-route` | 带 scope CAS 的受管 route apply。 |
| POST | `/api/actions/approval/provider-events` | HMAC provider 批准/拒绝 callback。 |

会话请求只接受服务、版本、精确 Action/文件、`inputPolicyDigest`、`sideEffectCeiling` 和可选 TTL/次数。caller、approver、status、per-Action sourceDigest 和 scopeDigest 都由服务端派生，客户端不得提交。

## Callback 签名

body 只允许：

```json
{
  "eventId": "evt-001",
  "sessionId": "<sessionId>",
  "decision": "APPROVED",
  "issuedAt": "2026-08-13T09:00:00Z",
  "nonce": "nonce-001",
  "approverId": "security-reviewer"
}
```

签名原文按 LF 连接：

```text
v1
POST
/api/actions/approval/provider-events
{epochSeconds}
{eventId}
{nonce}
{sha256(rawBody)}
```

请求头使用 `X-LightESB-Approval-Key-Id`、`X-LightESB-Approval-Timestamp`、`X-LightESB-Approval-Event-Id`、`X-LightESB-Approval-Nonce` 和 `X-LightESB-Approval-Signature: v1=<hmac-sha256>`。服务端重验 header/body、时钟、approver allowlist、eventId 和 nonce 防重放。

## 失败处理

- `PENDING/REJECTED/REVOKED/EXPIRED/EXHAUSTED/COMPLETED/STALE` 都不能执行受管 apply。
- digest conflict 表示读取后发生并发变化，应重新 GET；不要覆盖提交。
- `STALE` 或 reapproval required 表示出现未归因目录变化，必须创建新会话重新审批。
- transition unavailable 表示 apply 没有改变任何受批 Action digest；修正候选，不消耗旧批准绕过。
- rollback failed/unavailable 时停止自动重试，保留 sessionId、operationId 和脱敏错误证据供人工排障。

会话、provider event 和 transition 都写安全审计；输出和持久化不含 bearer、HMAC secret、callback raw body、route/input 正文或绝对路径。
