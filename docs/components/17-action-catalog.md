# 服务 Action 声明与离线索引

## 验收动作

1. 只修改服务事实源：`service.config.properties`、唯一 route XML 和 route metadata 明确引用的 schema。
2. 对单个服务执行离线校验并查看 descriptor：

```bash
python3 skills/lightesb-route-authoring/scripts/action-catalog.py \
  --service-dir lightesb-camel-app/{serviceName}/{serviceVersion}
```

3. 对严格两层 app 根目录生成确定性索引；输出必须位于任一服务版本目录之外：

```bash
python3 skills/lightesb-route-authoring/scripts/action-catalog.py \
  --app-root lightesb-camel-app \
  --output build/action-index.json
```

索引是可删除重建的派生产物，不是第二份业务事实源。不要手工编辑或复制到 `lightesb-camel-app/{serviceName}/{serviceVersion}`。

## P0 边界

Action catalog 只做离线发现和静态校验，不创建运行时执行入口、授权、Token、数据库表、管理 API 或 Agent 自动调用能力。`agentCallable=true` 只表示未来执行通道的候选资格；实际调用仍需独立的认证、授权、审批和审计机制。

未声明 `actions.ids` 的历史服务在 app-root 批量模式中跳过；显式校验该服务时会按缺少声明失败。工具不会推断 action、schema、副作用、暴露范围或凭据。

## Properties 声明

Action 声明集中写入 `service.config.properties`，使用 UTF-8 单行 `key=value`：

```properties
actions.schema-version=1
actions.ids=order-check
action.order-check.route-id=order-check-route
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
| `example/routes/security-validation/DemoSecuritySrv/v1.0.0/` | `demo-security-check` | HTTP `requestReply`，entry request/response schema，Agent 候选 |
| `example/routes/AvevaMqttSrv/v1.0.0/` | `aveva-mqtt-telemetry` | MQTT `oneWayConsumer`，normalizer 后 schema，不可调用 |
| `example/routes/AvevaOpcUaSrv/v1.0.0/` | `aveva-opcua-telemetry` | OPC UA `oneWayConsumer`，DataValue 解包后 schema，不可调用 |

这些样例的静态通过不证明路由已加载、Broker/Server 已连接或现场协议互操作。运行态验证仍需按 HTTP、MQTT mock、OPC UA mock/现场分层执行。
