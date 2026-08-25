# Action 功能手动测试指南（交付包）

本文档是交付包 Action 能力的手工验收测试清单，面向在本交付目录内独立执行的测试 Agent 或测试人员。测试依据为随包文档：`components/17-action-catalog.md`、`action-allowlist-api.md`、`action-token-api.md`、`action-approval-api.md`、`action-authorization-api.md`、`action-execution-api.md`、`action-audit-api.md`。

**授权边界**：本文档本身不构成运行态操作授权。修改 `lightesb-camel-app/lightesb-config.properties`、复制/移除演示服务、启动/重启 LightESB、调用管理 API 或业务 HTTP 接口、执行 CLI 远程写操作前，必须由操作者在当前测试任务中明确确认范围。测试只针对本机交付目录，不连接任何外部系统；完成后按恢复步骤处理环境。

**测试范围**：Action 离线目录（validate/build）、在线目录只读查询、控制面认证授权边界、精确 allowlist、短期 token、统一授权 dry-run、安全执行、有界任务会话审批（含 HMAC callback 与受管 route apply）、追加式审计查询。

## 1. 前置检查

- 工作目录为交付包根目录（含 `start.sh`、`lightesb-camel-1.0.0.jar`、`lightesb-cli.jar`）。
- `java -version` 可用（Java 21）；`curl`、`sha256sum`、`openssl` 可用。
- 8080（管理/控制面）与 18082（演示服务 HTTP 入口）端口未被占用：`ss -ltn | grep -E ':(8080|18082)'` 应为空；若 8080 已有本交付包实例在运行，先停止。
- CLI 可用：`java -jar lightesb-cli.jar --help` 能输出命令列表。下文所有 `lightesb` 命令均等价于 `java -jar lightesb-cli.jar`。
- 确认当前没有正在运行的 LightESB 进程：`ps -ef | grep lightesb-camel-1.0.0.jar | grep -v grep`。

## 2. 部署演示 Action 服务

把随包样例复制为正式运行服务（热加载目录契约）：

```bash
cp -r example/routes/security-validation/DemoSecuritySrv lightesb-camel-app/
```

该服务声明了唯一可执行样例 Action：`demo-security-check@v1.0.0`（声明版本 2、`read + requestReply`、HTTP 入口 `POST http://localhost:18082/api/demo/security`、静态 `direct:` invocation、entry 输入/输出 JSON Schema，`approval-required=false`、`idempotency=none`）。

## 3. 配置 Action 开关与测试凭证

### 3.1 备份并生成测试 token

```bash
cp lightesb-camel-app/lightesb-config.properties /tmp/lightesb-config.properties.bak

# 生成三个控制面 token（高熵随机串）及其 sha256 digest（小写 hex）
for n in READ ADMIN EXEC; do
  T=$(openssl rand -hex 24)
  echo "LT_$n=$T  sha256=$(printf '%s' "$T" | sha256sum | cut -d' ' -f1)"
done
```

把输出保存到测试记录中（原 token 只在测试期间使用，服务端只保存 digest）。

### 3.2 追加 Action 配置

把以下配置追加到 `lightesb-camel-app/lightesb-config.properties` 末尾，把 `<SHA_READ>` / `<SHA_ADMIN>` / `<SHA_EXEC>` 替换为上一步的 digest：

```properties
# ===== Action 测试配置（测试后需移除） =====
lightesb.action-catalog.enabled=true
lightesb.action-security.enabled=true
lightesb.action-audit.enabled=true
lightesb.action-allowlist.enabled=true
lightesb.action-token.enabled=true
lightesb.action-approval.enabled=true
lightesb.action-authorization.enabled=true
lightesb.action-execution.enabled=true

lightesb.action-security.credentials[0].name=ops-read
lightesb.action-security.credentials[0].caller=ops-cli
lightesb.action-security.credentials[0].roles=catalog-read
lightesb.action-security.credentials[0].token-sha256=<SHA_READ>
lightesb.action-security.credentials[1].name=ops-admin
lightesb.action-security.credentials[1].caller=ops-admin
lightesb.action-security.credentials[1].roles=action-admin
lightesb.action-security.credentials[1].token-sha256=<SHA_ADMIN>
lightesb.action-security.credentials[2].name=agent-executor
lightesb.action-security.credentials[2].caller=agent-exec
lightesb.action-security.credentials[2].roles=action-execute
lightesb.action-security.credentials[2].token-sha256=<SHA_EXEC>

lightesb.action-approval.hmac.provider-name=test-provider
lightesb.action-approval.hmac.key-id=test-key-1
lightesb.action-approval.hmac.secret=action-test-hmac-secret-0123456789abcdef
lightesb.action-approval.hmac.allowed-approver-ids[0]=security-reviewer
```

注意：这些是 Spring 配置，必须重启生效，不能依赖热加载；caller/name 只允许小写字母、数字、中划线；digest 必须互不相同。

### 3.3 启动并自检

```bash
nohup ./start.sh > logs/action-test-console.log 2>&1 &
```

等待启动完成（约 30–60 秒），逐项确认：

- `curl -s http://localhost:8080/actuator/health` 返回 `UP`。
- `logs/lightesb.log` 无 `invalid Action credential` 等启动失败；若有 credential 配置错误应用会启动失败，需修正 digest 格式后重启。
- `logs/lightesb.log` 出现 `DemoSecuritySrv` 路由加载成功（`demo-security-route`、`demo-security-invocation-route`）。
- HTTP 入口直连可用：

```bash
curl -s -X POST http://localhost:18082/api/demo/security \
  -H 'Content-Type: application/json' -d '{"orderId":"ORD0000000001"}'
# 预期：{"code":"OK","message":"validated"}
```

### 3.4 配置 CLI profile

```bash
lightesb profile add --name action-read  --server http://localhost:8080 --token '<LT_READ>'
lightesb profile add --name action-admin --server http://localhost:8080 --token '<LT_ADMIN>'
lightesb profile add --name action-exec  --server http://localhost:8080 --token '<LT_EXEC>'
```

后续命令用 `--profile <name>` 指定身份。

### 3.5 注册服务管理关系

运行目录热加载和 Action Catalog 不会代替服务管理注册。G7 的会话受管 route apply 还会校验 provider、输入/输出消息和目标服务关系，因此在首次测试时创建以下记录；重复测试前先用 `service list/get` 查询并复用已有记录，不要重复创建同名数据。

先准备接入系统和两个非空消息模型：

```bash
mkdir -p build

cat > build/demo-security-app.json <<'JSON'
{
  "clientId": "DemoSecurityTest",
  "appName": "Demo Security Action Test",
  "vendor": "LightESB"
}
JSON

cat > build/demo-security-request-message.json <<'JSON'
{
  "msgName": "DemoSecurityRequest",
  "msgType": "REQUEST",
  "msgStandard": "JSON",
  "msgVersion": "V1.0",
  "msgStructureJson": "{\"orderId\":\"ORD0000000001\"}",
  "msgStructure": [{
    "nodeName": "orderId",
    "nodeDesc": "Order identifier",
    "nodeType": "STRING",
    "nodeLength": "64",
    "ifRequired": "1",
    "nodeList": []
  }]
}
JSON

cat > build/demo-security-response-message.json <<'JSON'
{
  "msgName": "DemoSecurityResponse",
  "msgType": "RESPONSE",
  "msgStandard": "JSON",
  "msgVersion": "V1.0",
  "msgStructureJson": "{\"code\":\"OK\",\"message\":\"validated\"}",
  "msgStructure": [
    {
      "nodeName": "code",
      "nodeDesc": "Result code",
      "nodeType": "STRING",
      "nodeLength": "32",
      "ifRequired": "1",
      "nodeList": []
    },
    {
      "nodeName": "message",
      "nodeDesc": "Result message",
      "nodeType": "STRING",
      "nodeLength": "128",
      "ifRequired": "1",
      "nodeList": []
    }
  ]
}
JSON

lightesb app create --file build/demo-security-app.json --yes --output json
lightesb message create --file build/demo-security-request-message.json --yes --output json
lightesb message create --file build/demo-security-response-message.json --yes --output json
```

记录三个命令返回的 app ID、请求消息 ID 和响应消息 ID。把消息 ID 填入服务定义后创建服务：

```bash
REQUEST_MESSAGE_ID='<请求消息创建返回的 ID>'
RESPONSE_MESSAGE_ID='<响应消息创建返回的 ID>'

cat > build/demo-security-service.json <<JSON
{
  "serviceCnname": "Demo Security Action Test Service",
  "serviceName": "DemoSecuritySrv",
  "serviceVersion": "v1.0.0",
  "serviceImpl": "REST",
  "serviceStatus": "STOPPED",
  "serviceTypes": [],
  "serviceTags": [],
  "serviceDescription": "Local Action approval managed route apply test service",
  "servicePermissions": "TEST",
  "serviceCall": "SYNC",
  "serviceProvider": "DemoSecurityTest",
  "serviceInId": "$REQUEST_MESSAGE_ID",
  "serviceOutId": "$RESPONSE_MESSAGE_ID",
  "serviceDeploymentStatus": "DEPLOYED"
}
JSON

lightesb service create --file build/demo-security-service.json --yes --output json
lightesb service list --service-name DemoSecuritySrv --output json
lightesb service get --id '<服务创建返回的 ID>' --output json
```

预期：服务版本为 `v1.0.0`，provider 为 `DemoSecurityTest`，`serviceInId`/`serviceOutId` 分别指向刚创建的消息。记录服务 ID，恢复环境时先删除服务，再删除消息和接入系统。`msgStructure` 不能为空；空数组会被服务端以“消息结构不能为空”拒绝。

## 4. 阶段 A：离线目录命令（不依赖服务端）

目录和 CLI/API 使用 `v1.0.0`；服务配置属性使用 `service.version=1.0.0`。当前交付目录含根级共享资源目录 `TransformDS`，app-root 命令必须显式排除它。

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| A1 | `lightesb action validate --service-dir lightesb-camel-app/DemoSecuritySrv/v1.0.0` | 退出码 0；stdout 为 canonical JSON，含 `demo-security-check` descriptor |
| A2 | `lightesb action validate --app-root lightesb-camel-app --exclude-root TransformDS` | 退出码 0；共享资源目录被显式排除，未声明 `actions.ids` 的服务被跳过，DemoSecuritySrv 通过 |
| A3 | `lightesb action validate --service-dir <任选一个未声明 actions.ids 的服务版本目录>` | 退出码 65，输出稳定 `ACTION_*` 错误码 |
| A4 | `lightesb action build --app-root lightesb-camel-app --exclude-root TransformDS --out build/action-index.json --yes` | 退出码 0；`build/action-index.json` 存在且含 demo-security-check 条目；文件不在任何服务版本目录内 |
| A5 | `lightesb action build --app-root lightesb-camel-app --out lightesb-camel-app/DemoSecuritySrv/v1.0.0/x.json --yes` | 失败：输出目录拒绝落在服务版本目录内 |

## 5. 阶段 B：在线目录只读查询与认证边界

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| B1 | `lightesb --profile action-read action status --output json` | 200；返回目录状态与 revision |
| B2 | `lightesb --profile action-read action list --page-num 1 --page-size 20 --output json` | 200；含 `demo-security-check`，状态 VALID 且运行态 AVAILABLE |
| B3 | `lightesb --profile action-read action search --query security --output json` | 200；命中 demo-security-check |
| B4 | `lightesb --profile action-read action get --action-id demo-security-check --service-version v1.0.0 --output json` | 200；descriptor 含 routeId、invocation、schema 摘要、相对 source location；不含配置实值、token、绝对路径 |
| B5 | 无 bearer：`curl -s http://localhost:8080/api/actions/status` | 401 `ACTION_AUTH_REQUIRED` |
| B6 | 伪造 token：`curl -s -H 'Authorization: Bearer wrong-token' http://localhost:8080/api/actions/status` | 401 `ACTION_AUTH_INVALID` |
| B7 | 越权：`lightesb --profile action-read action allowlist list` | 403 `ACTION_AUTH_FORBIDDEN`（catalog-read 不继承 action-admin） |
| B8 | 分页 revision：B2 第一页取 `revision` 后 `action list --page-num 2 --page-size 1 --expected-revision <revision>`；若条目不足 2 页可用 `--page-size 1` 翻页 | revision 一致时正常返回；热加载后 revision 变化时请求失败（记录现象即可） |

## 6. 阶段 C：精确 Allowlist（action-admin）

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| C1 | `lightesb --profile action-admin action allowlist add --credential-name agent-executor --action-id demo-security-check --service-version v1.0.0 --yes --output json` | 200；返回 policyId、caller=`agent-exec`、enabled=true；不含 credentialName、token/digest |
| C2 | 重复执行 C1 | 409 `ACTION_ALLOWLIST_CONFLICT` |
| C3 | `lightesb --profile action-admin action allowlist list --limit 50 --output json` | 200；含 C1 策略；响应只有安全字段 |
| C4 | `lightesb --profile action-admin action allowlist disable --policy-id <policyId> --yes` 后再 `enable` | 均 200；幂等重复 enable 不重复审计 |
| C5 | `lightesb --profile action-admin action allowlist add --credential-name agent-executor --action-id not-exist --service-version v1.0.0 --yes` | 422 `ACTION_ALLOWLIST_ACTION_INELIGIBLE` 或 400；不创建策略 |
| C6 | 用 `--profile action-exec`（action-execute）执行 allowlist list | 403 `ACTION_AUTH_FORBIDDEN` |

确保 C 阶段结束时策略处于 enabled 状态（D/E/F 阶段依赖）。

## 7. 阶段 D：短期运行 Token

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| D1 | `lightesb --profile action-exec action token issue --action demo-security-check@v1.0.0 --ttl-seconds 600 --yes --output json` | 200；`data.token` 为 `lat_` 前缀，仅本次可见。立即保存为测试变量 `LAT_TOKEN`，并记录 `tokenId` |
| D2 | `lightesb --profile action-exec action token introspect --token-id <tokenId> --output json` | 200；含 fingerprint、caller=agent-exec、精确 actions、status=ACTIVE；不含原 token/hash |
| D3 | 越界 scope：`lightesb --profile action-exec action token issue --action demo-security-check@v9.9.9 --yes` | 422 `ACTION_TOKEN_SCOPE_INELIGIBLE`（不在目录与 allowlist 交集） |
| D4 | 运行 token 调控制面：`curl -s -H "Authorization: Bearer $LAT_TOKEN" http://localhost:8080/api/actions/audit-events` | 401/403，运行 token 与控制面隔离 |
| D5 | 撤销：`lightesb --profile action-exec action token revoke --token-id <tokenId> --yes`，再 introspect | 200；status=REVOKED、含 revokedAt；重复 revoke 幂等 |
| D6 | 撤销后分别调用 E 阶段的 dry-run 和 F 阶段的 execute | dry-run 返回 HTTP 200、`data.allowed=false`、`data.reason=TOKEN_REVOKED`；execute 返回 HTTP 401、错误码 `ACTION_AUTHORIZATION_TOKEN_REVOKED`。两者均不执行 Action。随后按 D1 重新签发一个 token 供后续阶段使用 |

## 8. 阶段 E/F：授权 Dry-run 与安全执行

准备请求文件：

```bash
cat > /tmp/action-input.json <<'EOF'
{"orderId": "ORD0000000001"}
EOF
cat > /tmp/action-input-policy.json <<'EOF'
{"type":"object","required":["orderId"],"properties":{"orderId":{"type":"string"}},"additionalProperties":false}
EOF
```

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| E1 | dry-run 正向：`curl -s -X POST http://localhost:8080/api/actions/authorization:dry-run -H "Authorization: Bearer $LAT_TOKEN" -H 'Content-Type: application/json' -d '{"actionId":"demo-security-check","serviceVersion":"v1.0.0","inputPolicy":{"type":"object","required":["orderId"],"properties":{"orderId":{"type":"string"}},"additionalProperties":false},"input":{"orderId":"ORD0000000001"}}'` | 200 且 `data.allowed=true`；含 required `auditId`、`sourceDigest`、`routeGeneration`、policy/input digest；不含执行许可字段 |
| E2 | dry-run 输入越界：把 input 改为 `{"foo":"bar"}` | 200 且 `allowed=false`，reason 说明输入不满足策略/schema；接口保持 200 闭合诊断 |
| E3 | dry-run 用控制面 token：`-H "Authorization: Bearer <LT_ADMIN>"` | 401/403（该端点只接受 `lat_` 运行 token） |
| F1 | 执行：`LIGHTESB_ACTION_TOKEN="$LAT_TOKEN" lightesb action execute --action-id demo-security-check --service-version v1.0.0 --input-file /tmp/action-input.json --input-policy-file /tmp/action-input-policy.json --yes --output json` | 200；`data.output` = `{"code":"OK","message":"validated"}`；含 `sourceDigest`、`routeGeneration`、`inputDigest`、`outputDigest`、`authorizationAuditId`、`executionAuditId`、`durationMs` |
| F2 | 执行输入非法：input 文件改为 `{"foo":"bar"}` 后重试 | 非 2xx，稳定 `ACTION_*` 错误码（输入 schema/策略拒绝）；记录实际错误码 |
| F3 | 执行不带 `--yes` | 拒绝执行并提示确认（CLI 确认语义） |
| F4 | 输出越界对照：直连 HTTP（3.3 节命令）返回同样 JSON，证明 Action 执行与 HTTP 入口复用同一 invocation 链 | 两者 output 一致 |

说明：`demo-security-check` 为 `read` 且 `approval-required=false`，执行不需要审批会话；G 阶段单独验证会话能力。

## 9. 阶段 G：审批会话、HMAC callback 与受管 route apply

### G1 请求会话（action-execute profile）

```bash
POLICY_DIGEST=$(sha256sum /tmp/action-input-policy.json | cut -d' ' -f1)
lightesb --profile action-exec action approval session request \
  --service-name DemoSecuritySrv --service-version v1.0.0 \
  --action-id demo-security-check \
  --allowed-file demo-security-route.xml \
  --allowed-file common.config.properties \
  --allowed-file service.config.properties \
  --allowed-file response-schema.json \
  --input-policy-digest "$POLICY_DIGEST" \
  --side-effect-ceiling read \
  --ttl-seconds 900 --max-transitions 5 --max-executions 10 \
  --yes --output json
```

预期：200，返回 `sessionId`、status=`PENDING`。记录 sessionId。

### G2 模拟外部审批 provider 批准（HMAC callback）

```bash
SESSION_ID='<G1 的 sessionId>'
BODY=$(printf '{"eventId":"evt-001","sessionId":"%s","decision":"APPROVED","issuedAt":"%s","nonce":"nonce-001","approverId":"security-reviewer"}' \
  "$SESSION_ID" "$(date -u +%Y-%m-%dT%H:%M:%SZ)")
TS=$(date +%s)
BODY_SHA=$(printf '%s' "$BODY" | sha256sum | cut -d' ' -f1)
SIG=$(printf 'v1\nPOST\n/api/actions/approval/provider-events\n%s\nevt-001\nnonce-001\n%s' "$TS" "$BODY_SHA" \
  | openssl dgst -sha256 -hmac 'action-test-hmac-secret-0123456789abcdef' -hex | awk '{print $NF}')
curl -s -X POST http://localhost:8080/api/actions/approval/provider-events \
  -H 'Content-Type: application/json' \
  -H 'X-LightESB-Approval-Key-Id: test-key-1' \
  -H "X-LightESB-Approval-Timestamp: $TS" \
  -H 'X-LightESB-Approval-Event-Id: evt-001' \
  -H 'X-LightESB-Approval-Nonce: nonce-001' \
  -H "X-LightESB-Approval-Signature: v1=$SIG" \
  -d "$BODY"
```

预期：200，事件被接受。随后：

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| G3 | `lightesb --profile action-exec action approval session get --session-id $SESSION_ID --output json` | status=`APPROVED`，含 `currentScopeDigest` |
| G4 | 重放：完全重复 G2 的 curl | 拒绝（eventId/nonce 防重放），记录错误码 |
| G5 | 篡改：改 BODY 中 decision 后沿用原签名 | 签名校验失败，拒绝 |
| G6 | 非法 approver：换 `approverId` 为未配置值并重新计算签名（换新 eventId/nonce） | 拒绝（approver 不在 allowlist） |

### G7 受管 route apply

先制造一处真实路由变更（改变受批 Action digest）：编辑 `lightesb-camel-app/DemoSecuritySrv/v1.0.0/demo-security-route.xml`，在 `demo-security-invocation-route` 的 `<process ref="jsonResponseProcessor"/>` 之前加一行 `<log message="action-test-${body}"/>`。

```bash
SCOPE=$(lightesb --profile action-exec action approval session get --session-id $SESSION_ID --output json | grep -o '"currentScopeDigest"[^,]*' )
# 从最新 session JSON 取 currentScopeDigest 值填入：
lightesb --profile action-exec ai route apply \
  --file lightesb-camel-app/DemoSecuritySrv/v1.0.0/demo-security-route.xml \
  --save-remote \
  --service-name DemoSecuritySrv --service-version v1.0.0 \
  --route-file-name demo-security-route.xml \
  --resource-file common.config.properties \
  --resource-file service.config.properties \
  --resource-file response-schema.json \
  --action-session-id "$SESSION_ID" \
  --expected-scope-digest '<currentScopeDigest>' \
  --yes --output json
```

预期：apply 成功，transition 被记录；再次 `session get` 可见 scope digest 已更新、transition 计数 +1。验证路由仍正常：重复 3.3 节 HTTP 直连 curl，仍返回 validated。

`demo-security-route.xml` 通过 `lightesb.action.output.schema=response-schema.json` 声明输出契约，所以 `response-schema.json` 必须同时出现在 G1 allowlist 和 G7 resources 中。`--resource-file response-schema.json` 只写文件名时，会相对 `--file` 指定的 route XML 所在目录解析，无需重复完整服务目录。

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| G8 | 用旧的 scope digest 重复 G7 | 409 digest conflict；不得回退普通 apply |
| G9 | 直接手工编辑 `service.config.properties`（如改 description 任意值）触发热加载，再 `session get` | 会话变为 `STALE` 或要求重新审批；此后受管 apply 被拒绝 |
| G10 | `lightesb --profile action-exec action approval session complete --session-id $SESSION_ID --yes`（若 G9 后已 STALE 可用 revoke） | 200；终态后 get 显示 COMPLETED/REVOKED，不能再 apply |
| G11 | 新会话请求用 `--profile action-read` | 403（request 需要 action-execute） |

## 10. 阶段 H：审计查询

```bash
curl -s -H 'Authorization: Bearer <LT_ADMIN>' \
  'http://localhost:8080/api/actions/audit-events?limit=50'
```

| 编号 | 步骤 | 预期 |
| --- | --- | --- |
| H1 | 无过滤查询 | 200；包含前面阶段产生的 `POLICY_CREATED`、`TOKEN_ISSUED`、`TOKEN_REVOKED`、`CATALOG_GET`、授权/执行/审批事件；字段固定（auditId、caller、actionId、eventType、result、digest、durationMs、createdAt），无业务 body、无 token 原文 |
| H2 | 过滤：`?eventType=TOKEN_ISSUED&result=SUCCESS&caller=agent-exec` | 只返回匹配事件 |
| H3 | 分页：`?limit=1` 取 `nextCursor`，再 `?limit=1&cursor=<nextCursor>` | `hasMore`/`nextCursor` 行为正确；改变过滤条件后复用旧 cursor 返回 400 `INVALID_ACTION_AUDIT_CURSOR` |
| H4 | `--profile action-read` 调同一端点 | 403 `ACTION_AUTH_FORBIDDEN` |

## 11. 恢复环境

```bash
# 只删除本轮 3.5 新建的服务管理记录；仍被其他测试复用时不要删除
lightesb service delete --id '<服务 ID>' --yes
lightesb message delete --id '<请求消息 ID>' --yes
lightesb message delete --id '<响应消息 ID>' --yes
lightesb app delete --id '<接入系统 ID>' --yes

# 停止 LightESB
pkill -f 'lightesb-camel-1.0.0.jar'
# 还原配置
cp /tmp/lightesb-config.properties.bak lightesb-camel-app/lightesb-config.properties
# 移除演示服务与测试产物
rm -rf lightesb-camel-app/DemoSecuritySrv build/action-index.json /tmp/action-input.json /tmp/action-input-policy.json
```

CLI 没有 profile 删除命令；`action-read`/`action-admin`/`action-exec` 三个 profile 保存的测试 token 在配置还原后已在服务端失效，可保留或用 `profile add` 同名覆盖。

说明：H2 中的 Action 表（`ACTION_AUDIT_LOG`、`ACTION_ALLOWLIST_POLICY`、`ACTION_RUNTIME_TOKEN*`、`ACTION_APPROVAL_*`、`ACTION_AUTHORIZATION_IDEMPOTENCY`）由服务端自动建表，测试数据保留在 `H2Database/data/tempdb.mv.db`，不影响关闭开关后的正常运行；如需彻底清空须先停服务再由人工处理数据库文件。

## 12. 结果记录模板

| 阶段 | 用例 | 结果(通过/失败) | 实际现象/错误码 | 备注 |
| --- | --- | --- | --- | --- |
| A | A1..A5 | | | |
| B | B1..B8 | | | |
| C | C1..C6 | | | |
| D | D1..D6 | | | |
| E/F | E1..E3, F1..F4 | | | |
| G | G1..G11 | | | |
| H | H1..H4 | | | |

排障入口：服务日志 `logs/lightesb.log`、启动控制台 `logs/action-test-console.log`、服务目录 `lightesb-camel-app/DemoSecuritySrv/v1.0.0/logs/`；H2 控制台 `http://localhost:8080/h2-console`（JDBC URL `jdbc:h2:file:./H2Database/data/tempdb`，用户 `sa`，空密码）。常见错误码对照见各 `action-*-api.md` 文档末尾表格。
