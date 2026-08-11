# Action 短期 Token API

## 启用

显式开启 catalog、security、audit、allowlist 和 token 五个开关；token 默认关闭：

```properties
lightesb.action-catalog.enabled=true
lightesb.action-security.enabled=true
lightesb.action-audit.enabled=true
lightesb.action-allowlist.enabled=true
lightesb.action-token.enabled=true
lightesb.action-token.default-ttl-seconds=300
lightesb.action-token.max-ttl-seconds=3600
```

签发 credential 要有 `action-execute`，只能为自身服务端 caller 签发。`action-execute` 可查看/撤销自身 token，`action-admin` 可查看/撤销任意 token。运行 token 不能调用控制面 API。

## API 与 CLI

| Endpoint | Method | 请求 |
| --- | --- | --- |
| `/api/actions/tokens` | POST | 可选 `ttlSeconds`；1–50 个精确 `actions[]`。 |
| `/api/actions/tokens/{tokenId}` | GET | 无。 |
| `/api/actions/tokens/{tokenId}:revoke` | POST | 无 body，幂等。 |

```bash
lightesb action token issue --action payment.lookup@v1 --ttl-seconds 300 --yes
lightesb action token introspect --token-id <tokenId>
lightesb action token revoke --token-id <tokenId> --yes
```

issue 的 `data.token` 只显示一次；立即写入调用方 secret store。introspect/revoke 只返回 tokenId、fingerprint、caller、精确 actions、issuedAt、expiresAt、status、revokedAt，不返回原 token/hash/digest。请求不接受 caller、credentialName、token、digest、通配符或未知字段。

服务端只保存 256-bit 随机 token 的 SHA-256。每个签发 scope 必须处于当前目录与精确 allowlist 交集。issue/revoke 与 required audit 同事务；introspect 使用 best-effort audit。

错误码：`INVALID_ACTION_TOKEN_REQUEST`（400）、`ACTION_TOKEN_FORBIDDEN`（403）、`ACTION_TOKEN_NOT_FOUND`（404）、`ACTION_TOKEN_SCOPE_INELIGIBLE`（422）、`ACTION_TOKEN_UNAVAILABLE`（503）、`ACTION_AUDIT_UNAVAILABLE`（503），认证失败沿用 `ACTION_AUTH_*`。

该能力只管理短期授权材料，不执行 Action，不提供 list/renew/delete、审批、OAuth2 或 MCP。
