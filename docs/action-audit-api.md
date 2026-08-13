# Action 追加式审计查询 API

## 启用

在平台运行配置中显式开启审计与 Action security，并配置只保存 digest 的管理员 credential：

```properties
lightesb.action-audit.enabled=true
lightesb.action-security.enabled=true
lightesb.action-security.credentials[0].name=ops-audit
lightesb.action-security.credentials[0].caller=ops-auditor
lightesb.action-security.credentials[0].roles=action-admin
lightesb.action-security.credentials[0].token-sha256=${LIGHTESB_ACTION_AUDIT_TOKEN_SHA256:}
```

原 token 只保存在调用方 secret store，通过 `Authorization: Bearer <token>` 发送。HTTP 查询要求 audit+security 双开关和精确 `action-admin`；`catalog-read`、`action-execute` 不继承权限。

若同时开启 `lightesb.action-catalog.enabled=true`，catalog status/list/search/get 的成功读取会 best-effort 追加安全事件。审计存储故障不会改变原目录查询响应。

精确 allowlist 的实际 add/enable/disable 状态变化使用 `POLICY_CREATED/POLICY_ENABLED/POLICY_DISABLED` required audit，并与策略写入同事务；审计失败时策略变化回滚。`POLICY_CHANGED` 保留为兼容事件值。

短期 token 的 issue/revoke 使用 `TOKEN_ISSUED/TOKEN_REVOKED` required audit 并与状态写入同事务；introspect 使用 `TOKEN_INTROSPECTED` best-effort audit。事件只保存 `sha256(tokenId)`，不保存 bearer token/hash。

## 查询

```bash
curl -H 'Authorization: Bearer <original-token>' \
  'http://localhost:8080/api/actions/audit-events?caller=ops-reader&eventType=catalog_get&result=success&limit=50'
```

| Endpoint | Method | 参数 |
| --- | --- | --- |
| `/api/actions/audit-events` | GET | 可选 `caller`、`actionId`、`serviceVersion`、`eventType`、`result`、`limit`、`cursor`。 |

`limit` 默认 50、最大 200。结果按创建时间和 auditId 倒序；`hasMore=true` 时保留原过滤条件并把 `nextCursor` 回传下一页。cursor 与过滤条件绑定，改变过滤条件后必须从第一页开始。

标准响应的 `data` 为：

```json
{
  "items": [
    {
      "auditId": "75f24a91e2394f87b82040f19642ad93",
      "caller": "ops-reader",
      "actionId": "payment.lookup",
      "serviceVersion": "v1",
      "sourceDigest": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "inputDigest": null,
      "eventType": "CATALOG_GET",
      "result": "SUCCESS",
      "policyRef": null,
      "tokenIdHash": null,
      "approvalIdHash": null,
      "errorCode": null,
      "durationMs": 3,
      "createdAt": "2026-08-11T08:00:00Z"
    }
  ],
  "hasMore": false,
  "nextCursor": null
}
```

事件固定列不包含业务 body、request/response payload、header、credential、原 token、任意 details/metadata JSON 或异常正文。

## 错误与边界

| HTTP | code | 处理 |
| --- | --- | --- |
| 400 | `INVALID_ACTION_AUDIT_QUERY` | 修正字段、枚举、长度或 limit。 |
| 400 | `INVALID_ACTION_AUDIT_CURSOR` | cursor 非法或过滤条件已变化；从第一页重试。 |
| 401 | `ACTION_AUTH_REQUIRED` / `ACTION_AUTH_INVALID` | 提供有效 bearer。 |
| 403 | `ACTION_AUTH_FORBIDDEN` | 使用具有精确 `action-admin` 的 credential。 |
| 503 | `ACTION_AUDIT_UNAVAILABLE` | 稍后重试并检查控制面数据库。 |

当前没有公开审计写入、清理、修改、删除、retention 或归档 API。审批和执行服务只通过内部 required append 写固定安全事件；审计查询本身不授予审批或执行权限。
