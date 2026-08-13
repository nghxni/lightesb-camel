# Action 安全执行 API

## 启用

真实执行默认关闭，必须显式同时开启：

```properties
lightesb.action-catalog.enabled=true
lightesb.action-security.enabled=true
lightesb.action-audit.enabled=true
lightesb.action-allowlist.enabled=true
lightesb.action-token.enabled=true
lightesb.action-approval.enabled=true
lightesb.action-authorization.enabled=true
lightesb.action-execution.enabled=true
```

当前只执行声明版本 2、`read + requestReply`、HTTP 入口、带静态 `direct:` invocation 和 JSON 输入/输出 Schema 的 Action。write/destructive、one-way、工业协议、动态 endpoint 和 MCP 不在范围。

## API

```http
POST /api/actions/execute
Authorization: Bearer lat_<43位base64url字符>
Content-Type: application/json
```

```json
{
  "actionId": "demo-security-check",
  "serviceVersion": "v1.0.0",
  "inputPolicy": {
    "type": "object",
    "required": ["orderId"],
    "properties": {"orderId": {"type": "string"}}
  },
  "input": {"orderId": "ORD0000000001"}
}
```

可选字段为 `sessionId` 和 `idempotencyKey`。Body 拒绝重复/未知字段、尾随 JSON 和超限输入。运行 token 与控制面 bearer 隔离；这个精确 POST 使用运行 token，其他 `/api/actions/**` 仍按控制面角色保护。

服务端重新验证 token、allowlist、Catalog、输入 Schema/策略、审批和幂等边界，在精确服务版本锁内消费一次性许可，只调用当前 CamelContext 中 descriptor 已证明的静态 direct route。输出必须是受限 JSON 并满足当前 output Schema。任何客户端字段都不会参与 endpoint 拼接。

成功数据包含 `actionId`、`serviceName`、`serviceVersion`、`sourceDigest`、`routeGeneration`、`inputDigest`、`output`、`outputDigest`、`authorizationAuditId`、`executionAuditId` 和 `durationMs`。除 `output` 外不返回业务正文；不返回 token、permit、Camel 异常或绝对路径。

主要执行错误：

| HTTP | 错误码 |
| --- | --- |
| 409 | `ACTION_EXECUTION_GENERATION_CHANGED`、`ACTION_EXECUTION_INVOCATION_MISMATCH` |
| 502 | `ACTION_EXECUTION_OUTPUT_INVALID`、`ACTION_EXECUTION_OUTPUT_LIMIT_EXCEEDED`、`ACTION_EXECUTION_OUTPUT_SCHEMA_UNAVAILABLE`、`ACTION_EXECUTION_OUTPUT_SCHEMA_STALE`、`ACTION_EXECUTION_OUTPUT_SCHEMA_VIOLATION`、`ACTION_EXECUTION_ROUTE_FAILED` |
| 503 | `ACTION_EXECUTION_RUNTIME_NOT_RUNNING`、`ACTION_EXECUTION_INVOCATION_UNAVAILABLE`、`ACTION_EXECUTION_EXECUTION_UNAVAILABLE`、`ACTION_EXECUTION_AUDIT_UNAVAILABLE` |
| 504 | `ACTION_EXECUTION_TIMEOUT` |

授权错误沿用 `ACTION_AUTHORIZATION_*`。超时或 completion audit 不可用表示结果不确定；首版只允许 read Action。

## CLI

```bash
export LIGHTESB_ACTION_TOKEN='lat_<运行token>'
lightesb action execute \
  --action-id demo-security-check \
  --service-version v1.0.0 \
  --input-file request.json \
  --input-policy-file input-policy.json \
  --yes --output json
```

`--input/--input-file` 二选一，`--input-policy/--input-policy-file` 二选一。默认从 `LIGHTESB_ACTION_TOKEN` 读取运行 token，也可用 `--runtime-token-env` 选择其他环境变量。`--runtime-token` 仅用于明确的临时调用，可能暴露在进程列表中。CLI 不发送 profile 控制面 bearer，不回显 runtime token 或 input。

## 限额配置

| 配置 | 默认值 | 范围 |
| --- | --- | --- |
| `lightesb.action-execution.timeout-ms` | `5000` | 100–30000 |
| `lightesb.action-execution.max-output-bytes` | `1048576` | 1024–2097152 |
| `lightesb.action-execution.max-output-depth` | `64` | 1–128 |
| `lightesb.action-execution.max-output-nodes` | `10000` | 1–100000 |

审计只保存安全标识、摘要、结果、时延和稳定错误码，不保存 request/output body、header 或 raw token。
