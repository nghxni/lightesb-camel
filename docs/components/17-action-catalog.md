# 服务 Action 声明与离线索引

## 使用与校验

1. 只修改服务事实源：`service.config.properties`、唯一 route XML 和 route metadata 明确引用的 schema。
2. 对单个服务执行离线校验并查看 descriptor：

```bash
java -jar lightesb-cli.jar action validate \
  --service-dir lightesb-camel-app/{serviceName}/{serviceVersion}
```

版本目录和 CLI/API 参数使用 `vX.Y.Z`，例如 `v1.0.0`；`service.config.properties` 中的 `service.version` 使用不带 `v` 的 `X.Y.Z`，例如 `service.version=1.0.0`。生成的 Action descriptor 仍使用目录版本 `vX.Y.Z`。

3. 对严格两层 app 根目录生成确定性索引；输出必须位于任一服务版本目录之外：

```bash
java -jar lightesb-cli.jar action build \
  --app-root lightesb-camel-app \
  --out build/action-index.json \
  --yes
```

app 根目录下不含版本子目录的共享资源目录（例如 `TransformDS` 共享 DataSonnet 函数库）不参与目录生成，用 `--exclude-root <目录名>`（可重复或逗号分隔）显式排除。

索引是可删除重建的派生产物，不是第二份业务事实源。不要手工编辑或复制到 `lightesb-camel-app/{serviceName}/{serviceVersion}`。

## 功能边界

随包 `lightesb-cli.jar` 的 `action validate/build` 提供离线发现、静态校验和索引生成；`action status/list/search/get` 通过受保护管理 API 查询已发布的内存快照。这些命令不执行 Action。`validate` 只向标准输出写规范 JSON，`build` 必须显式使用 `--yes`，并以原子替换写入服务目录外。`agentCallable=true` 只表示该 Action 允许进入调用候选集合，不授予实际调用权限；真实执行仍必须通过独立认证、allowlist、审批、精确授权和审计。

服务端另提供默认关闭的启动快照基础。现场确需为后续运行时目录能力准备内存视图时，可在平台运行配置中显式设置：

```properties
lightesb.action-catalog.enabled=true
```

启用后，只有已成功进入 `RUNNING` 的服务版本才能发布 Action。XML/properties 变化跟随路由加载结果成对刷新；descriptor 明确引用的 schema，以及编译失败登记的缺失/无效 schema，创建、修改或删除后会强制重载当前服务版本。新代校验失败时该服务 Action 不可见；缺失 schema 补回后可由目录监听自愈。

只读查询接口只消费该内存快照，不读取远端服务目录。热加载验证时应同时检查服务仍为 `RUNNING` 且日志出现新的 Action generation/revision；失败时检查 quarantine 错误码，不继续使用旧 descriptor。

服务端的 Action 控制面身份边界和只读 Controller 都默认关闭。启用在线查询时必须同时开启两个开关，并只保存高熵原 token 的 SHA-256 digest：

```properties
lightesb.action-security.enabled=true
lightesb.action-security.credentials[0].name=ops-read
lightesb.action-security.credentials[0].caller=ops-cli
lightesb.action-security.credentials[0].roles=catalog-read
lightesb.action-security.credentials[0].token-sha256=${LIGHTESB_ACTION_CREDENTIAL_0_SHA256:}
```

原 token 只保存在调用方 secret store，并通过 `Authorization: Bearer <token>` 发送。name/digest 必须唯一；同 caller 的旧、新轮换 credential 只能使用完全相同的 role 集。显式开启但 credential 为空时所有 Action 路径都返回 401；配置格式、重复或角色映射冲突时应用启动失败。`catalog-read`、`action-admin`、`action-execute` 不做隐式继承。

未声明 `actions.ids` 的服务在 app-root 批量模式中跳过；显式校验该服务时返回退出码 `65` 和稳定 `ACTION_DECLARATION_VERSION_INVALID`。工具不会推断 action、schema、副作用、暴露范围或凭据。

## 在线只读查询

把原 token 保存到 CLI profile，服务端只配置其 digest：

```bash
lightesb profile add --name action-read --server http://localhost:8080 --token '<original-token>'
lightesb profile use action-read
lightesb action status
lightesb action list --page-num 1 --page-size 20
lightesb action search --query security --page-num 1 --page-size 20
lightesb action get --action-id demo-security-check --service-version v1.0.0
```

list/search 的 `pageSize` 默认 20、最大 100。第一页返回 `revision`，第二页及后续页必须用 `--expected-revision` 回传；若热加载已产生新 revision，CLI 返回 HTTP 失败，自动化必须丢弃旧页并从第一页重新读取。同一 actionId 存在多版本时，get 必须指定 `--service-version`。

`--output json` 保留标准响应与 `requestId`。返回内容只包含安全 descriptor、状态、generation、digest 和相对 source location，不包含配置实值、原 token、credential digest 或服务器绝对路径。status/list/search/get 只要求 `catalog-read`，不接受自报 caller，也不执行 Action。

## 追加式审计

需要留存 Action 控制面发现事件时，显式开启：

```properties
lightesb.action-audit.enabled=true
```

catalog status/list/search/get 成功读取会 best-effort 追加固定安全事件；审计存储故障不改变原查询结果。查询审计还要求 `lightesb.action-security.enabled=true` 和精确 `action-admin` credential，通过 `GET /api/actions/audit-events` 读取。

审计表只允许追加和查询，不提供清理、修改或删除 API。事件不含请求/响应 body、header、原 token、任意 details 或异常正文；完整参数、响应和错误码见 [Action 追加式审计查询 API](../action-audit-api.md)。审计能力本身不执行 Action；审批会话是独立、默认关闭的控制面能力。

## 精确 allowlist

需要为后续受控调用维护精确资格时，显式开启 `lightesb.action-allowlist.enabled=true`，并同时开启 catalog、security、audit。策略只允许精确 caller+actionId+serviceVersion；caller 由服务端 credential name 映射，客户端不能自报。add/enable 会重验当前 descriptor 的 Agent exposure、callable、VALID 和 AVAILABLE；disable 在目录故障时仍可安全收窄。

策略变化与 required audit 同事务。allowlist 本身只管理资格，不执行 Action，也不提供 wildcard/block/delete。API、CLI 与错误码见 [Action 精确 Allowlist 管理 API](../action-allowlist-api.md)。

## 短期 Action token

五开关显式开启后，可用 `action token issue/introspect/revoke` 管理短期不透明 token。原 token 只在 issue 成功响应出现一次，服务端只保存 SHA-256；scope 必须位于当前目录与精确 allowlist 交集。运行 token 与控制面 bearer 隔离，不能调用控制面 API。详见 [Action 短期 Token API](../action-token-api.md)。

## 有界任务会话审批

六开关显式开启后，可用 `action approval session request/get/revoke/complete` 管理人工批准的有界任务范围。会话绑定单一服务版本、精确 Action/文件、输入策略摘要、副作用上限、TTL 和次数预算；批准/拒绝只接受 allowlist approver 的 HMAC callback。

多 Action 会话逐项保存真实 source digest，并用聚合 scope digest 做整组 CAS。只有带 session/scope digest 的 Action 专用受管 route apply，经过备份、热加载和 Catalog 结果证明后才延续 lineage；普通 apply 或直接文件变化会使旧会话 `STALE`。会话不执行 Action，也不是 bearer；详见 [Action 有界任务会话审批](../action-approval-api.md)。

## 统一授权 Dry-run

七开关显式开启后，可用精确 `POST /api/actions/authorization:dry-run` 对运行 token、当前目录/allowlist、审批会话、输入策略、Action entry Schema、幂等声明和 generation 做闭合诊断。该端点使用 `lat_` token，不使用控制面 bearer；dry-run 写 required audit，但不执行 route、不消费会话或幂等状态，也不返回执行许可。策略是有大小/深度/节点门禁且禁止引用、组合器、条件和正则的 JSON Schema 子集。详见 [Action 统一授权 Dry-run](../action-authorization-api.md)。

## Action 安全执行

八开关显式开启后，可用精确 `POST /api/actions/execute` 或 `action execute --yes` 执行声明版本 2 的 `read + requestReply` HTTP Action。必须使用独立 `lat_` 运行 token，profile 控制面 bearer 不能替代它。服务端在同一请求内重验 token、allowlist、审批范围、输入 Schema、source digest 和 route generation，再原子消费一次性许可并调用由 descriptor 派生的静态 `direct:` endpoint。

执行范围不包含 `write`、`destructive`、one-way、MQTT、OPC UA、动态 endpoint 或 MCP。输出要通过字节、深度、节点和 output Schema 校验；completed/failed 审计为 required，不保存输入/输出正文、raw token 或内部异常。详见 [Action 安全执行 API](../action-execution-api.md)。

## Properties 声明

Action 声明集中写入 `service.config.properties`，使用 UTF-8 单行 `key=value`：

```properties
actions.schema-version=2
actions.ids=order-check
action.order-check.route-id=order-check-route
action.order-check.invocation-route-id=order-check-invocation-route
action.order-check.name=Order validation
action.order-check.description=Validate an order and return the result
action.order-check.interaction-pattern=requestReply
action.order-check.agent-callable=true
action.order-check.side-effect=read
action.order-check.idempotency=none
action.order-check.retry-policy=none
action.order-check.approval-required=false
action.order-check.exposure=agent
action.order-check.required-config-keys=server.port
action.order-check.credential-aliases=
action.order-check.required-scopes=
```

关键约束：

- `actionId` 只允许小写字母、数字和中划线，并以字母开头。
- `interaction-pattern`：`requestReply`、`oneWayProducer`、`oneWayConsumer`、`scheduled`。
- `side-effect`：`read`、`write`、`destructive`。
- `idempotency`：`none`、`supported`、`required`；`retry-policy`：`none`、`safe`、`idempotent`。
- `exposure`：`internal`、`api`、`agent` 或规范顺序 `api,agent`。
- `oneWayConsumer` 与 `scheduled` 必须 `agent-callable=false`；`agent-callable=true` 只允许 `requestReply`/`oneWayProducer` 且 exposure 含 `agent`。
- 声明版本 1 只提供目录描述；当前可执行绑定使用版本 2，并且只开放 `read + requestReply`。这类 Action 必须填写 `invocation-route-id`，指向同一 XML 内入口为静态 `direct:` 的独立 route。
- `invocation-route-id` 只填写 route ID，不填写 URI。目录编译器从该 route 派生 `direct:` ref；HTTP、`seda:`、占位符、参数和动态 endpoint 一律拒绝，不能用外部 HTTP 回环代替。
- `write`/`destructive` 必须显式声明幂等、重试和审批语义；`destructive` 必须审批、禁止重试且不可 agent-callable。
- 列表只写配置键名、凭据别名或 scope，不写密码、Token、Cookie、客户地址或配置实值。

## Route metadata 与 schema

metadata 位于目标 `<route>` 内、唯一 `<from>` 之前。HTTP 同步 Action 同时声明输入和输出：

```xml
<route id="order-check-route">
  <routeProperty key="lightesb.action.input.schema" value="request-schema.json"/>
  <routeProperty key="lightesb.action.input.media-type" value="application/schema+json"/>
  <routeProperty key="lightesb.action.input.contract-stage" value="entry"/>
  <routeProperty key="lightesb.action.output.schema" value="response-schema.json"/>
  <routeProperty key="lightesb.action.output.media-type" value="application/schema+json"/>
  <from uri="undertow:http://0.0.0.0:{{server.port}}/api/orders/check?httpMethodRestrict=POST"/>
  <to uri="direct:orderCheckInvocation"/>
</route>
<route id="order-check-invocation-route">
  <from uri="direct:orderCheckInvocation"/>
  <!-- 真实业务处理链放在这里，HTTP 入口和 Action 执行复用同一逻辑。 -->
</route>
```

协议 consumer 的 JSON schema 如果描述 processor 之后的 envelope，必须绑定 `normalized` stage 和准确 processor ref；它没有同步输出 schema：

```xml
<routeProperty key="lightesb.action.input.schema" value="telemetry-schema.json"/>
<routeProperty key="lightesb.action.input.media-type" value="application/schema+json"/>
<routeProperty key="lightesb.action.input.contract-stage" value="normalized"/>
<routeProperty key="lightesb.action.input.contract-processor-ref" value="mqttTelemetryNormalizeProcessor"/>
```

schema 必须位于当前服务版本目录内、由 metadata 显式引用且是有效 JSON object。OPC UA Milo `DataValue`、MQTT 原始 payload 等非 JSON 入口不能直接用 normalized JSON schema 冒充。

## 输出与安全边界

索引格式由 `skills/lightesb-route-authoring/scripts/action-index.schema.json` 固定，包含服务/action/route、协议和安全 URI 模板、契约摘要、配置键名、错误来源、相对 source locations 与 source digest。

工具不会解析占位符或输出配置值。工业入口中的 broker、endpoint、node、username、password、clientId 必须使用安全占位符；clientId 可在占位符后追加受限固定后缀。动态 `toD` 目标只记录 `component=dynamic` 和配置键名，不输出地址。symlink、路径穿越、DOCTYPE/entity、schema 越界/缺失、重复 action/route 绑定、未知枚举、consumer callable 和敏感 query 实值均失败。

## 交付样例

| 样例 | Action | 契约 |
| --- | --- | --- |
| `example/routes/security-validation/DemoSecuritySrv/v1.0.0/` | `demo-security-check` | HTTP `requestReply`，entry request/response schema，声明为 agent 调用候选但不授予权限 |
| `example/routes/AvevaMqttSrv/v1.0.0/` | `aveva-mqtt-telemetry` | MQTT `oneWayConsumer`，normalizer 后 schema，不可调用 |
| `example/routes/AvevaOpcUaSrv/v1.0.0/` | `aveva-opcua-telemetry` | OPC UA `oneWayConsumer`，DataValue 解包后 schema，不可调用 |

这些样例的静态通过不证明路由已加载、Broker/Server 已连接或现场协议互操作。运行态验证仍需按 HTTP、MQTT mock、OPC UA mock/现场分层执行。
