# Action 统一授权 Dry-run

## 启用

该能力默认关闭。现场必须同时显式开启 catalog、security、audit、allowlist、token、approval 和 authorization：

```properties
lightesb.action-catalog.enabled=true
lightesb.action-security.enabled=true
lightesb.action-audit.enabled=true
lightesb.action-allowlist.enabled=true
lightesb.action-token.enabled=true
lightesb.action-approval.enabled=true
lightesb.action-authorization.enabled=true
```

## 调用

```http
POST /api/actions/authorization:dry-run
Authorization: Bearer lat_<runtime-token>
Content-Type: application/json
```

```json
{
  "actionId": "payment-create",
  "serviceVersion": "v1.0.0",
  "sessionId": "8f9d7f76d8684bb79dc8b9edfb4a5204",
  "idempotencyKey": "payment-request-0001",
  "inputPolicy": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {"amount": {"type": "number", "maximum": 100}},
    "required": ["amount"],
    "additionalProperties": false
  },
  "input": {"amount": 10}
}
```

运行 token 与控制面 bearer 隔离。只有这一条精确 POST 使用 `lat_` token；其他 `/api/actions/**` 仍要求控制面 credential。

## 策略与限制

- `inputPolicy` 是受限 Draft 2020-12 Schema，只允许 type/properties/required/additionalProperties/enum/const、数值/长度/数组界限、uniqueItems 和单 schema items。
- 禁止引用、组合器、条件、正则和未知 keyword。
- policy 最多 16 KiB、深度 16、节点 256；input 默认最多 1 MiB、深度 64、节点 10000。
- 服务端还会验证当前服务版本目录中的 entry Action Schema 和文件摘要；越界、symlink 或热加载后摘要变化会拒绝。
- write/destructive、审批必需或带 outbound step 的 Action 必须提供已批准会话；幂等字段按 Action descriptor 的 required/supported/none 执行。

## 响应与失败处理

HTTP 200 的 `data.allowed` 是闭合诊断，`reason` 说明 token、目录、输入、审批、幂等或 generation 拒绝原因。响应包含 required `auditId`、当前 sourceDigest/routeGeneration 和 policy/input digest，但不包含执行许可。

Dry-run 不执行 route，不消费会话次数、幂等 key 或许可，不能被缓存为执行授权。Token、Catalog 或策略依赖异常如果仍能安全归类并写入 required audit，接口保持 200，通过 `allowed=false` 和 reason 返回闭合 decision；400 表示 bearer 或请求结构非法，只有无法完成闭合 decision 或 required audit 时才返回 503，此时必须停止自动化。日志、响应和数据库不得保存 raw token、幂等原值、input/policy 正文或绝对路径。

真实执行使用独立 `action-execution-api.md` 和 `action execute` CLI，由服务端重新终检并消费内部一次性许可；不能把 dry-run 响应转换成客户端许可。
