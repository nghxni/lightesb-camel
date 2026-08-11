# Action 精确 Allowlist 管理 API

## 启用

```properties
lightesb.action-catalog.enabled=true
lightesb.action-security.enabled=true
lightesb.action-audit.enabled=true
lightesb.action-allowlist.enabled=true
```

四个开关缺一不可。所有端点要求精确 `action-admin` bearer；新增策略只提交服务端配置的 `credentialName`，服务端据此派生目标 caller，并要求目标 credential 具有 `action-execute`。不要提交 caller、token、digest 或额外字段。

## Endpoint

| Endpoint | Method | 输入 |
| --- | --- | --- |
| `/api/actions/policies/allowlist` | GET | 可选 `limit`、`cursor`。 |
| `/api/actions/policies/allowlist` | POST | `credentialName`、`actionId`、`serviceVersion`。 |
| `/api/actions/policies/allowlist/{policyId}:enable` | POST | 无 body。 |
| `/api/actions/policies/allowlist/{policyId}:disable` | POST | 无 body。 |

```bash
curl -H 'Authorization: Bearer <action-admin-token>' \
  -H 'Content-Type: application/json' \
  -d '{"credentialName":"agent-executor","actionId":"payment.lookup","serviceVersion":"v1"}' \
  http://localhost:8080/api/actions/policies/allowlist
```

list 默认 50、最大 200，按创建时间和 policyId 倒序；`hasMore=true` 时将 `nextCursor` 回传下一页。策略响应固定为 policyId、caller、actionId、serviceVersion、enabled、createdBy/updatedBy、createdAt/updatedAt，不含 credentialName、token/digest、配置值或目录路径。

## 安全与事务边界

allowlist 只能收窄当前 Action 目录资格。add/enable 要求 descriptor exposure 含 Agent、可调用、VALID 且运行态 AVAILABLE；disable 在目录暂不可用时仍可执行。策略实际变化与 `POLICY_CREATED/POLICY_ENABLED/POLICY_DISABLED` required audit 同事务，审计失败会回滚策略变化。重复 add 返回冲突；幂等 enable/disable 不重复审计。

该 API 不提供 wildcard、block、delete、Action 执行、token 签发或审批。

## 错误码

| HTTP | code |
| --- | --- |
| 400 | `INVALID_ACTION_ALLOWLIST_REQUEST` / `INVALID_ACTION_ALLOWLIST_CURSOR` / `ACTION_ALLOWLIST_TARGET_INVALID` |
| 401 | `ACTION_AUTH_REQUIRED` / `ACTION_AUTH_INVALID` |
| 403 | `ACTION_AUTH_FORBIDDEN` |
| 404 | `ACTION_ALLOWLIST_NOT_FOUND` |
| 409 | `ACTION_ALLOWLIST_CONFLICT` |
| 422 | `ACTION_ALLOWLIST_ACTION_INELIGIBLE` |
| 503 | `ACTION_ALLOWLIST_UNAVAILABLE` / `ACTION_AUDIT_UNAVAILABLE` |
