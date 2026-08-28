# CLI 命令压缩参考

## 定位

CLI 的远程命令调用 LightESB 控制面 API 和本地配置，不承载 Camel 运行时，不绕过服务端状态机。`action validate/build` 是纯离线命令，`action status/list/search/get` 是受 bearer 保护的在线只读命令；受控本地写还包括 `action build` 把派生索引写到服务目录外，以及 `ai route prepare` 把服务端 content 持久化基线的最小闭包写入新候选目录。本地写操作必须加 `--yes` 并校验真实路径边界；prepare 不覆盖已存在目标。

## 安装与入口

```bash
java -jar lightesb-cli.jar --help
java -jar lightesb-cli.jar --version
java -jar lightesb-cli.jar service package build --help
alias lightesb='java -jar /path/to/lightesb-cli.jar'
```

顶层、命令组和叶子命令都支持 `-h/--help`。

## 全局参数

| 参数 | 说明 |
| --- | --- |
| `--server http://host:port` | 单次命令指定服务端 |
| `--profile <name>` | 使用本地 profile |
| `--output table|json` | 输出格式，CI 优先 `json` |
| `--yes` | 写操作确认 |
| `--file payload.json` | 从 JSON 文件读取输入 |
| `--ai-token <token>` | 用于服务端 AI 日志问答等 AI 管控接口的 `X-AI-Token` |

## Action 目录

```bash
lightesb action validate --service-dir lightesb-camel-app/DemoSrv/v1.0.0
lightesb action validate --app-root lightesb-camel-app
lightesb action validate --app-root lightesb-camel-app --exclude-root TransformDS
lightesb action build --app-root lightesb-camel-app --out build/action-index.json --yes
lightesb action status
lightesb action list --page-num 1 --page-size 20
lightesb action search --query security --page-num 1 --page-size 20
lightesb action get --action-id demo-security-check --service-version v1.0.0
LIGHTESB_ACTION_TOKEN='lat_<运行token>' lightesb action execute --action-id demo-security-check --service-version v1.0.0 --input-file request.json --input-policy-file input-policy.json --yes --output json
```

`--service-dir` 与 `--app-root` 二选一。`validate` 只读并向标准输出写 canonical JSON；`build` 在全部目录通过校验后原子替换 `--out`，且拒绝把输出写入任一服务版本目录。这两个命令不连接服务端、不启动 Camel、不触发热加载或执行 Action。`--app-root` 模式要求严格两层目录；根级共享资源目录（例如 `TransformDS` 共享 DataSonnet 函数库）用 `--exclude-root <目录名>`（可重复或逗号分隔）显式排除，名称只允许单个根级目录名。成功退出码为 `0`，参数/确认错误为 `64`，目录契约失败为 `65` 并带稳定 `ACTION_*` 错误码。

在线四个命令使用 profile 的普通 token 作为 `Authorization: Bearer`，要求服务端双开关和 `catalog-read`。list/search 第二页起必须使用第一页输出的 `--expected-revision`；revision 变化时从第一页重试。`pageSize` 最大 100。在线命令只读内存快照，不读取远端文件、不提交 caller、不执行 Action；`--output json` 保留服务端标准响应。

精确 allowlist 管理使用 `action-admin` profile：

```bash
lightesb action allowlist list --limit 50 --output json
lightesb action allowlist add --credential-name agent-executor --action-id payment.lookup --service-version v1 --yes --output json
lightesb action allowlist disable --policy-id <policyId> --yes --output json
lightesb action allowlist enable --policy-id <policyId> --yes --output json
```

服务端必须同时开启 catalog、security、audit、allowlist。add 只选择服务端 credential name，不接受 caller；写操作要求 `--yes`。CLI 不提供 wildcard/block/delete 或数据库直连，也不执行 Action。list 默认 50、最大 200，下一页使用 `--cursor <nextCursor>`。

短期 token 要求五开关与 `action-execute` self / `action-admin` any 权限：

```bash
lightesb action token issue --action payment.lookup@v1 --ttl-seconds 300 --yes
lightesb action token introspect --token-id <tokenId>
lightesb action token revoke --token-id <tokenId> --yes
```

有界任务会话：

```bash
lightesb action approval session request --service-name OrderSrv --service-version v1.0.0 --action-id order-check --allowed-file OrderSrv-route.xml --allowed-file common.config.properties --allowed-file service.config.properties --input-policy-digest <sha256> --side-effect-ceiling write --ttl-seconds 900 --max-transitions 5 --max-executions 10 --yes --output json
lightesb action approval session get --session-id <sessionId> --output json
lightesb action approval session revoke --session-id <sessionId> --yes
lightesb action approval session complete --session-id <sessionId> --yes
```

request/revoke/complete 要求 `--yes`，get 只读。CLI 不接受 caller、approver、状态、source/scope digest override 或 callback secret，也不签 approve/reject。会话只表达任务范围，不执行 Action。`STALE` 会话不能 complete/apply/执行，只能创建新会话重审或对原会话执行 revoke 收口。

`--action` 可重复。issue 原 token 只显示一次；introspect/revoke 不输出 token/hash/digest。命令不接受 `--caller`、`--credential-name` 或 raw token。

安全执行要求八个 Action 开关全部显式开启，仅支持声明版本 2 的 `read + requestReply` HTTP Action。`--input|--input-file` 和 `--input-policy|--input-policy-file` 各自二选一；必要时增加 `--session-id` 或 `--idempotency-key`。`execute` 必须带 `--yes`，只使用 `LIGHTESB_ACTION_TOKEN`、`--runtime-token-env` 指定的环境变量或显式 `--runtime-token`，不发送 profile 的控制面 bearer。CLI 不保存或回显 token，也不接受 URI、generation、digest 或 caller 覆盖。

## Profile 与 Doctor

```bash
lightesb profile add --name dev --server http://localhost:8080
lightesb profile use dev
lightesb profile current
lightesb profile list
lightesb doctor
lightesb doctor --server http://localhost:8080 --output json
lightesb robot doctor --offline
lightesb robot doctor --offline --output json
lightesb robot doctor --runtime --server http://localhost:8080
lightesb robot doctor --runtime --server http://localhost:8080 --output json
lightesb robot list
lightesb robot list --site-id site-a --robot-type quadruped --online true
lightesb robot get --robot-id quad-001
lightesb robot capabilities --robot-id quad-001
lightesb robot state --robot-id quad-001
lightesb robot audit --robot-id quad-001
lightesb robot audit --robot-id quad-001 --command-id cmd-001 --event-type robot.command.submitted
lightesb robot command validate --file command.json
lightesb robot command validate --file command.json --output json
lightesb robot command status --robot-id quad-001 --command-id cmd-001
lightesb robot command status --robot-id quad-001 --command-id cmd-001 --output json
lightesb robot command submit --file command.json --yes
lightesb robot command submit --file command.json --yes --output json
lightesb robot inference decision-status --robot-id quad-001 --decision-id vaid_0123456789abcdef0123456789abcdef
lightesb robot inference decision-status --robot-id quad-001 --decision-id vaid_0123456789abcdef0123456789abcdef --output json
lightesb robot inference submit --robot-id quad-001 --decision-id vaid_0123456789abcdef0123456789abcdef --yes --output json
lightesb robot command ingest-receipt --receipt-type ack --topic robot/site-a/quad-001/command/cmd-001/ack --payload-file ack.json --yes
lightesb robot command ingest-receipt --receipt-type result --topic robot/site-a/quad-001/command/cmd-001/result --payload-json '{"commandId":"cmd-001","robotId":"quad-001","siteId":"site-a","status":"succeeded"}' --yes --output json
lightesb diagnostics snapshot
lightesb diagnostics snapshot --component route-runtime --output json
lightesb diagnostics snapshot --service-name DemoSrv --service-version v1.0.0 --output json
lightesb diagnostics warnings
lightesb diagnostics warnings --component service-log --output json
```

`profile current/list --output json` 只返回 `server`、`tokenConfigured` 和 `aiTokenConfigured` 等状态，不输出 token 值；配置不存在时只读 profile 命令不会创建文件。

`doctor` 只做环境和只读 API 检查，不修改服务端状态。

`diagnostics snapshot/warnings` 只调用：

```text
GET /api/diagnostics/runtime-snapshot
```

可选过滤参数为 `serviceName`、`serviceVersion` 和 `component`。当前组件包括 `route-runtime`、`service-log`、`ai-route-cache`、`ai-model-session`、`external-datasource`、`robot-command`、`instance-log`。该命令面向 Codex 和人工远程排查；不读取远程文件系统，不触发重载、清理、关闭连接或日志级别调整。`--output json` 会保留服务端标准响应，包含 `requestId`、`components` 和服务端生成的 `warnings`。

服务端以 `lightesb.route.enabled=false` 启动时，`route-runtime` 组件不注册；排查机器人命令 dispatcher 使用 `--component robot-command`。

`instance-log` 只输出实例日志 writer 的存储类型、H2 fallback 状态、实例日志查询存储、JsonKeyword 查询存储、队列、批次、拒绝任务、最近 flush 和最近错误，不输出请求/响应正文。

无 MySQL POC 演示时，服务端设置：

```properties
lightesb.poc.h2-fallback.enabled=true
```

然后用以下命令确认 H2 fallback：

```bash
lightesb diagnostics snapshot --component instance-log --output json
lightesb diagnostics snapshot --component robot-command --output json
```

期望 `pocH2FallbackEnabled=true`，且相关存储字段为 `h2-fallback`。

`robot doctor --offline` 只做机器人接入静态检查，输出 PASS/WARN/FAIL 和 `connectivityChecked=false`；不连接真实 endpoint，不下发机器人命令，不调用验证 route。

`robot doctor --runtime` 只调用 `GET /api/diagnostics/runtime-snapshot?component=robot-command`，输出管理面运行态 doctor 检查项。检查项覆盖数据库表存在性、outbox 积压、状态快照陈旧、补偿积压、启用 denylist 策略和最近错误码分布。`--output json` 保留服务端标准 envelope；table 输出展示 `overallStatus`、`connectivityChecked=false`、检查项和 warning。该命令不连接真实 endpoint、不下发命令、不调用验证 route，不能解释为真实资产在线、最近心跳健康或现场错误日志已检查。

`RobotEdgeInferenceSrv` 当前是 `direct:` + `mock:` 样例，没有对外 HTTP/MQTT/gRPC 推理 API。`robot inference` 只调用控制面 decision 查询/提交 API，不调用该 route；不得使用普通 `robot command submit` 绕过 AI reservation。

`robot list/get/capabilities/state/audit` 只调用：

```text
GET /service-management/v1/robots
GET /service-management/v1/robots/{robotId}
GET /service-management/v1/robots/{robotId}/capabilities
GET /service-management/v1/robots/{robotId}/state
GET /service-management/v1/robots/{robotId}/audit
GET /service-management/v1/robots/{robotId}/commands/{commandId}
```

这些命令是只读查询，不提交动作，不清理审计数据，不连接真实协议 endpoint。`robot state` 文本输出包含 `onlineStatus`、`protocolProfile`、`lastCommandId`、`lastErrorCode`、`sourceType` 和 `updatedAt`；`--output json` 保留服务端完整标准响应。状态快照可能来自命令状态、ack/result 派生或管理面样例快照，不代表真实设备在线验收。

批量状态快照分页查询当前直接使用管理 API `GET /service-management/v1/robots/state-snapshots`，支持 `siteId`、`onlineStatus`、`health`、`protocolProfile`、`pageNum`、`pageSize`；CLI 暂不新增对应命令。

补偿积压分页查询当前直接使用管理 API `GET /service-management/v1/robots/compensations`；CLI 暂不新增对应命令。远程排查优先用 `lightesb diagnostics snapshot --component robot-command --output json` 查看 `compensationRequired` 和 `lastCompensationRequired`。

禁用策略 CLI：

```text
lightesb robot policy list --server http://localhost:8080 --scope-type site --enabled true
lightesb robot policy add --server http://localhost:8080 --scope-type robot --scope-value quad-001 --reason "maintenance" --yes
lightesb robot policy enable --server http://localhost:8080 --id <policyId> --yes
lightesb robot policy disable --server http://localhost:8080 --id <policyId> --yes
```

这些命令只调用 `GET/POST /service-management/v1/robots/policies/denylist` 及 `POST /service-management/v1/robots/policies/denylist/{id}:enable|disable`。写操作必须带 `--yes`，会写控制面审计。命中启用策略时，`commands:validate` 和 `commands` 返回 `ROBOT_POLICY_REJECTED`，不会触发协议调用。

当前默认用本机 WSL mock HTTP 和本地测试验证，不证明真实资产库、真实在线状态、真实审计源、真实协议执行状态或真实能力发现。

`robot command validate --file` 从 JSON 文件读取 `robotId`，只调用：

```text
POST /service-management/v1/robots/{robotId}/commands:validate
```

它用于命令预检，不调用 `/commands`，不创建命令记录，不连接 MQTT、rosbridge、OPC UA、Modbus、Kafka、WMS/MES，也不写执行审计。服务端会检查 schema、能力、denylist 和共享高层命令安全策略；`move_to` 覆盖区域/速度，已配置的 `pick/place` 覆盖工位/互锁/载荷。策略拒绝返回 `ROBOT_POLICY_REJECTED`，预检通过不代表现场互锁或设备执行已验证。`--output json` 保留服务端标准响应。

`robot command status --robot-id --command-id` 只查询已有命令结果，不调用 `POST /commands`，不创建新命令。`--output json` 保留服务端标准响应。

`robot command submit --file --yes` 只调用：

```text
POST /service-management/v1/robots/{robotId}/commands
```

它会提交到服务端命令入口，必须显式传 `--yes`，并拒绝 `mode=validate_only` 和 `dryRun=true`。服务端返回 `protocolReceipt.outboxStatus=pending` 时，只表示命令已进入可靠派发队列；`protocolReceipt.dispatched=false` 不能当作机器人已收到或已执行。

`robot inference decision-status --robot-id --decision-id` 调用 decision GET 入口，返回脱敏 `persistedStatus/effectiveStatus` 与摘要。`robot inference submit --robot-id --decision-id --yes` 调用同路径的 `:submit` POST，请求体固定为 `{}`。CLI 不提供 approve/reject、不传候选命令、不计算 HMAC。完整契约见 `docs/robot-ai-approval-api.md`。

`robot command ingest-receipt --receipt-type ack|result --topic --payload-file|--payload-json --yes` 只调用：

```text
POST /service-management/v1/robots/mqtt-receipts:ingest
```

CLI 会向管理 API 发送 `receiptType`、`topic` 和原始 `payloadJson`。`--receipt-type` 只允许 `ack` 或 `result`；`--payload-file` 与 `--payload-json` 必须二选一；该命令可能推进命令状态并写审计，所以必须显式传 `--yes`。CLI 不订阅 MQTT topic，不连接 broker，不提交命令，不派发 outbox，也不改写回执 payload。topic/payload 一致性、重复回执、乱序回执、状态合法性和审计事务边界由服务端校验。

## App 与 Message

```bash
lightesb app list
lightesb app list --client-id HIS
lightesb app get --id <appId>
lightesb app create --file app.json --yes
lightesb app update --file app.json --yes
lightesb app delete --id <appId> --yes

lightesb message list
lightesb message list --msg-type REQUEST
lightesb message request-response --msg-type RESPONSE
lightesb message get --id <messageId>
lightesb message create --file message.json --yes
lightesb message update --file message.json --yes
lightesb message delete --id <messageId> --yes
lightesb message structure xml --msg-name DemoRequest
lightesb message parse --file sample.json
lightesb message parse --file response.json --msg-type RESPONSE
lightesb message parse --file response.json --msg-type RESPONSE --root-node-name BusinessResponse
lightesb message parse --file sample.xml
lightesb message schema generate --id <messageId> --service-name DemoSrv --service-version v1.0.0 --schema-file request-schema.json --yes
lightesb message schema generate --file message.json --service-name DemoSrv --service-version v1.0.0 --schema-file request-schema.json --yes
lightesb message constraints
lightesb message domains
```

JSON 样例默认生成名为 `Request` 的 ROOT；`--msg-type RESPONSE` 将默认 ROOT 改为 `Response`。ROOT 节点的 `nodeName` 是生成 XML 时使用的实际根标签，可用 `--root-node-name <name>` 显式指定任意业务根名，且该输入优先于消息类型默认值。XML 样例保留自身根标签。

`message schema generate` 封装消息体 JSON Schema 预览接口：

- `POST /message-management/v1/json-schema/preview`
- `GET /message-management/v1/json-schema/preview/{id}`

`--id` 与 `--file` 必须且只能选择一个。`--app-dir` 默认是 `lightesb-camel-app`，目标 `{serviceName}/{serviceVersion}` 目录必须已存在。命令把 `data.schema` 写为该目录下的 `--schema-file`，写文件需要 `--yes`；`--output json` 返回实际写盘 `data.file`、服务版本目录相对且可直接用于路由的 `data.jsonSchemaPath`、`data.schema` 和 `data.warnings`。命令不会部署或重载服务。

自动生成校验路由时先用 `service list/get --output json` 查询服务关系。INPUT 取当前 `serviceInId`（同时可读 `serviceInName`），OUTPUT 取当前 `serviceOutId`（同时可读 `serviceOutName`）；CALLBACK 先把 `serviceCallbackId` 作为服务 ID 查询回调服务，再取回调服务的 `serviceInId`。服务权限同时返回 `servicePermissions` 编码和 `servicePermissionsName` 字典名称，例如 `140` 对应 `PUBLIC`。固定文件分别为 `request-schema.json`、`response-schema.json`、`callback-schema.json`。只使用服务端返回的 Schema；`warnings` 非空时停止自动 apply 并展示完整内容，只有用户明确确认后继续。

`app.json` 最小字段：

```json
{
  "clientId": "HIS",
  "appName": "医院信息系统",
  "vendor": "DemoVendor"
}
```

`message.json` 最小字段：

```json
{
  "msgName": "DemoRequest",
  "msgType": "REQUEST",
  "msgStandard": "JSON",
  "msgVersion": "V1.0",
  "msgStructureJson": "{\"orderId\":\"ORD0000000001\"}",
  "msgStructure": [{
    "nodeName": "orderId",
    "nodeDesc": "订单标识",
    "nodeType": "STRING",
    "nodeLength": "64",
    "ifRequired": "1",
    "nodeList": []
  }]
}
```

`msgStructure` 不能为空；最小创建样例也必须至少包含一个结构节点。

消息结构可同时记录内部节点名 `nodeName` 和外部字段别名 `alias`。内部节点名必须以字母开头且只包含字母和数字；外部 JSON 字段包含下划线等合法别名字符时，不要直接把它作为内部节点名。例如需要保留外部字段 `same_as_shipping` 时，可配置：

```json
{
  "nodeName": "sameAsShipping",
  "alias": "same_as_shipping",
  "nodeType": "VARCHAR2",
  "nodeList": []
}
```

生成 JSON Schema 和样例 JSON 时，有别名则优先使用 `alias`，没有别名才使用 `nodeName`；内部持久化和节点定位仍保留 `nodeName`。别名必须通过服务端校验，并且不能与同级节点名或其他别名冲突。创建后建议执行 `message get --id <messageId> --output json` 做只读回查，不要只检查创建命令是否成功。

别名只负责字段命名映射，不改变消息类型能力。当前模型没有独立布尔类型时，布尔样例会按 `VARCHAR2` 记录；原始值数组无法直接解析时，应显式建模为 `COLLECTION -> item -> value`。

## Service、Deploy、Route、Log

```bash
lightesb service list
lightesb service get --id <serviceId>
lightesb service create --file service.json --yes
lightesb service update --file service.json --yes
lightesb service delete --id <serviceId> --yes
lightesb service config preview --file service.json
lightesb service config save --file service.json --yes
lightesb service package preview --file package.json
lightesb service package build --file package.json --yes
lightesb service package deploy --file package.json --yes
lightesb service start --id <serviceId> --yes
lightesb service stop --id <serviceId> --yes
lightesb service export --local-server http://localhost:8080 --app-dir lightesb-camel-app --service-name DemoSrv --service-version v1.0.0 --out dist/DemoSrv-v1.0.0.lightesb-service.zip --yes
lightesb service import-plan --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip
lightesb service import --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip --skip-existing --yes
lightesb service sync-remote --server http://remote-host:8080 --local-server http://localhost:8080 --app-dir lightesb-camel-app --service-name DemoSrv --service-version v1.0.0 --keep-package --yes

lightesb deploy validate ./DemoSrv.zip
lightesb deploy upload ./DemoSrv.zip --yes
lightesb deploy upload ./DemoSrv.zip --no-auto-start --yes
lightesb deploy status <deploymentId>
lightesb deploy history --limit 20
lightesb deploy history --service-name DemoSrv --service-version 1.0.0 --limit 20

lightesb route info
lightesb route status
lightesb route mapping
lightesb route detail --file-key <fileKey>
lightesb route config --file-key <fileKey>
lightesb route reload-service --service-name DemoSrv --service-version 1.0.0 --yes
lightesb route reload-file --file-path /server/lightesb-camel-app/DemoSrv/v1.0.0/route.xml --yes
lightesb route unload --file-path /server/lightesb-camel-app/DemoSrv/v1.0.0/route.xml --yes

lightesb log status
lightesb log health
lightesb log services
lightesb log level set --service-key DemoSrv@1.0.0 --level DEBUG --yes
lightesb log cleanup --yes
lightesb log cleanup --manual --yes
lightesb log instance list --service-name DemoSrv --service-version 1.0.0
lightesb log instance list --service-name DemoSrv --service-version 1.0.0 --keyword patientId=10001
lightesb log instance get --instance-uuid <instanceUuid>
lightesb log instance download --instance-uuid <instanceUuid> --type req
lightesb log instance download --instance-uuid <instanceUuid> --type res > response-body.txt

lightesb keyword list --service-name DemoSrv --service-version 1.0.0
lightesb keyword add --service-name DemoSrv --service-version 1.0.0 --key-name patientId --yes
lightesb keyword delete --id <keywordConfigId> --yes
lightesb keyword query-instances --service-name DemoSrv --service-version 1.0.0 --key-name patientId --json-value 10001
lightesb keyword query-instances --service-name DemoSrv --service-version 1.0.0 --key-name patientId --json-value 10001 --start-time "2026-06-01 00:00:00" --end-time "2026-06-01 23:59:59" --max-limit 100 --output json
```

`log instance` 与 `keyword` 的 `--service-name` 均使用服务英文名（也是服务目录名），例如 `DemoSrv`；中文展示名 `serviceCnName` 不作为查询标识。

`deploy history` 默认返回最近 50 条部署记录，可用 `--service-name` 和 `--service-version` 过滤单个服务版本。列表输出只包含概要，不拉取完整部署步骤日志。

`service start/stop` 等待服务端确认 Camel 上下文真实启动或卸载。部署状态为 `UNDEPLOYED` 时，`service start` 返回 HTTP `409 SERVICE_NOT_DEPLOYED`，应先生成并保存部署路由。同方向并发请求共享一次转换；相反方向、加载失败或超时会返回 HTTP `409` 并使 CLI 非零退出。超时不回滚 `server.running`，自动化脚本应查询服务状态或运行时诊断后再决定后续动作。成功结果中的 `idempotent=true` 表示没有重复写配置，`transitionReused=true` 表示复用了同方向任务。详见 [服务启停 API](../service-runtime-management-api.md)。

CLI 对 `service start/stop` 使用 130 秒 HTTP 请求超时，以覆盖服务端允许的 120 秒最大转换等待时间并接收结构化失败详情；其他命令仍使用默认 30 秒请求超时。

服务同步命令用于把本地服务版本迁移到远端 LightESB。导出包包含服务定义、接入系统、报文模型和服务目录文件，并在 manifest 中记录 metadata 与服务文件 `sha256`。`serviceVersion` 必须使用 `vX.Y.Z`。`service export` 会写本地包，必须加 `--yes`，并校验真实路径/符号链接边界后通过同目录临时文件原子替换。`import-plan` 只读远端状态；`import/sync-remote` 必须加 `--yes`。导入包拒绝路径穿越、重复 entry、服务目录不匹配和 SHA-256 不一致；包最大 50 MiB、最多 256 个 entry、单 entry 解压后最大 5 MiB、解压总量最大 50 MiB。`--skip-existing` 是默认幂等策略的显式写法。远端已有同名服务版本时默认跳过服务文件部署；需要覆盖时加 `--overwrite-service-files`。默认部署后自动启动路由；需要关闭时加 `--no-start`。`sync-remote --keep-package` 可保留中间导出包，也可用 `--package-out <path>` 指定路径。接入系统或服务定义冲突默认失败；需要更新时加 `--update-existing`。远端已有同名报文且内容不一致时会调用消息更新接口，远端当前 `msgVersion` 必须是 `V数字.单数字`，更新后递增单数字小版本并保留更新历史，例如 `V1.9` -> `V2.0`。

`deploy upload` 必须加 `--yes`，文件正文使用流式 multipart 发送；CLI 不提供
`--target-directory`，部署目标由服务端运行配置决定。服务端同时限制上传大小、
归档条目数、单文件解压大小、解压总量和目录深度。

`route reload-file/unload --file-path` 使用服务端路径，并且必须解析到服务端受管路由
根内真实存在的 XML 普通文件。`route config` 只返回相对服务目录，敏感配置值和
绝对路径显示为 `<redacted>`。

日志级别调整后立即生效，不需要执行日志重载。

`keyword` 命令域只调用 `/api/lightesb/json-keyword`，用于 Codex 和自动化快速处理 JSON 关键字配置：

- `list` 查询服务版本已注册 keyName。
- `add --yes` 新增关键字采集配置。
- `delete --id --yes` 删除错误配置，不影响历史采集数据。
- `query-instances` 按 `keyName/jsonValue` 反查实例 UUID；可选 `--start-time`、`--end-time`、`--max-limit` 和 `--output json`。

默认 MySQL 模式下，按关键字查询依赖服务端 JsonKeyword MySQL 同步链路和分表可用。无 MySQL POC 模式配置 `lightesb.poc.h2-fallback.enabled=true` 后，`keyword query-instances` 和 `log instance list --keyword key=value` 查询 H2 缓存表。

`service.json` 最小字段：

```json
{
  "serviceName": "DemoSrv",
  "serviceVersion": "1.0.0",
  "serviceProvider": "HIS",
  "serviceInId": "<requestMessageId>",
  "serviceOutId": "<responseMessageId>"
}
```

`serviceName` 是服务英文名和服务目录标识，只能包含字母、数字、下划线和中划线；中文展示名请写入 `serviceCnname`。

`package.json` 最小字段：

```json
{
  "serviceName": "DemoSrv",
  "serviceVersion": "1.0.0",
  "autoStart": true
}
```

## AI 命令

```bash
lightesb log ask "查询 PlatformHttp@v3.0.0@platform-http-route.xml 服务当前日志级别"
lightesb log ask --message "查询最近 10 分钟 DemoSrv 的失败实例" --memory-id ops-session-001
lightesb log ask --file ai-log-question.json

lightesb ai route generate --file ai-route.json
lightesb ai route generate --file ai-route.json --save-remote --return-logs --log-lines 80 --yes
lightesb ai route generate --file ai-route.json --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --yes
lightesb ai route read --service-name DemoAiSrv --service-version 1.0.0
lightesb ai route prepare --service-name DemoAiSrv --service-version v1.0.0 --out build/DemoAiSrv-v1.0.0-candidate --yes --output json
lightesb ai route validate --file build/DemoAiSrv-v1.0.0-candidate/DemoAiSrv-ai-route.xml --service-name DemoAiSrv --service-version v1.0.0 --route-file-name DemoAiSrv-ai-route.xml --resource-file common.config.properties --resource-file service.config.properties,input-transform.ds,request-schema.json --output json
lightesb ai route cache status
lightesb ai route cache clear --yes
lightesb ai route cache clear --service-name DemoAiSrv --service-version v1.0.0 --yes
lightesb ai route optimize --file ai-route-chat.json
lightesb ai route optimize --file ai-route-chat.json --save-remote --return-logs --log-lines 80 --yes
lightesb ai route optimize --file ai-route-chat.json --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --yes
lightesb ai route apply --file DemoAiSrv-route.xml --save-remote --service-name DemoAiSrv --service-version v1.0.0 --route-file-name DemoAiSrv-route.xml --resource-file common.config.properties --resource-file service.config.properties --resource-file request-schema.json --return-logs --log-lines 80 --timeout 30 --yes --output json
lightesb ai route apply --file build/DemoAiSrv-v1.0.0-candidate/DemoAiSrv-route.xml --save-remote --service-name DemoAiSrv --service-version v1.0.0 --route-file-name DemoAiSrv-route.xml --resource-file common.config.properties --resource-file service.config.properties --resource-file response-schema.json --action-session-id <sessionId> --expected-scope-digest <currentScopeDigest> --yes --output json
lightesb ai route apply --file route.xml --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --resource-file input-transform.ds --resource-file output-transform.ds --yes
lightesb ai diagnose
lightesb ai diagnose --service-name DemoAiSrv --service-version 1.0.0 --output json
```

`ai-route.json` 至少包含服务名、版本和自然语言需求：

```json
{
  "serviceName": "DemoAiSrv",
  "serviceVersion": "1.0.0",
  "routeFileName": "DemoAiSrv-ai-route.xml",
  "naturalLanguageRequirement": "生成一个 HTTP POST 演示路由，所有运行时行为必须体现为可见的 route.xml、properties、.ds 或资源文件。"
}
```

AI 边界：

- `log ask` 是可选服务端自然语言 Agent 能力，只把问题、`memoryId` 和 `X-AI-Token` 传给服务端，不在 CLI 本地推理日志语义；默认日志治理优先使用确定性 `log` 命令。
- `ai tool list/save/plan/run` 已删除；AI 路由生成统一走自然语言入口，最终以路由 XML、properties、`.ds` 和资源文件体现。
- `ai route generate` 要求输入 JSON 包含 `naturalLanguageRequirement`，默认只返回候选 XML/配置/资源，不写入 `lightesb-camel-app`，不保存配置，不自动部署；服务端先选择随包文档/skills 上下文，再生成 Artifact JSON，失败时返回服务端错误。上下文候选来自随包 `docs/README.md`，当前外发包运行目录主要过滤经验复盘类文档；未随包交付的内部材料不会作为生成候选。
- 服务端不使用内置配置键目录推断组件或过滤业务配置；组件形态、配置键写法和路由结构由模型根据自然语言需求与已选随包文档判断，后端只做 Artifact JSON、XML/route/tool 结构、平台运行配置边界和热加载校验。
- 上下文选择由服务端根据随包 `docs/README.md`、自然语言需求和候选清单完成。普通 HTTP 入站或 HTTP 下游调用默认只携带 HTTP 组件文档；只有明确要求路由日志、控制面 API、第三方管理调用、部署/回滚、日志调级、应用矩阵或已有样例时，才选择对应文档。服务端只对明显非生成必需的控制面和应用矩阵整篇文档做意图过滤，不用 Java 反推业务组件。
- 服务端默认不记录完整大模型输入输出；开发排障需要查看完整 prompt 和模型响应时，在服务端启用 `lightesb.ai.route.model.log-payload=true`，并把 `com.oureman.soa.lightesb.servicemanagement.AiRouteModelClient` 与 `com.oureman.soa.lightesb.config.ai.model.OpenAiResponsesChatModelFactory` 日志级别设为 DEBUG。该开关是服务端运行配置，不应写入 AI 路由生成的服务配置文件。
- 服务管理前端调用同一生成接口时，如果浏览器、代理或网关先超时但后端随后完成生成，可通过 `/service-management/v1/ai/route/generate/latest` 补取最近候选结果；CLI 生成命令仍以 `/generate` 同步响应为准。
- `ai route optimize` 默认只返回候选微调结果，不写入、不保存、不自动部署；服务端会生成或复用 baseline，再基于用户提交的当前 route/config/resources 微调。baseline 生成只携带自然语言需求、服务基础事实、必要运行配置摘要和已选文档；当前文件集和最近热部署失败诊断只进入最终微调步骤。微调步骤已得到可解析 Artifact JSON 且 Artifact 校验返回明确可修复诊断时，服务端会追加一次 validation repair；其他微调失败、不可修复策略错误或 repair 失败时返回 warning 和用户原始内容，不用 baseline 覆盖用户提交内容。
- `ai route prepare --out <new-candidate-dir> --yes` 只调用在线 content GET，把实际 route、两个 properties、route 实际引用的 `.ds` 和固定 Schema 作为整体发布到新本地目录。父目录必须真实存在，`--out` 必须不存在；命令拒绝 symlink 和当前工作目录下默认 `lightesb-camel-app`，但无法自动发现自定义或远程 Watcher 根。content/prepare 不证明服务已注册、路由已加载或 Action Catalog 与持久化目录一致。
- `ai route validate` 只调用候选校验 API，不需要 `--yes`，不写本地/远程文件、不热加载、不建立审批 lineage。裸 `--resource-file` 文件名相对 `--file` 所在候选目录解析；成功响应的 `savedFiles/deletedFiles` 用于确定随后会话的精确文件 allowlist。
- `ai route cache status` 查询服务端 AI 路由上下文选择、baseline 和最近生成结果缓存状态。
- `ai route cache clear --yes` 清理服务端 AI 路由缓存；带 `--service-name` 与 `--service-version` 时只清理指定服务关联缓存。
- `--save-remote --yes` 会调用服务端 `/service-management/v1/ai/route/apply`，由服务端备份、写入、等待 XML/properties 热加载并返回状态；CLI 不通过 SSH/SCP 或共享磁盘写远程文件。
- 远程 apply 返回 `APPLIED` 或 `APPLIED_DISABLED` 时，服务端同步把服务管理部署状态更新为 `SUCCESS`；失败或恢复路径不写入成功状态。
- `--return-logs` 控制成功时是否返回远程日志摘要；失败时即使未传 `--return-logs`，也会展示服务端返回的多个日志来源摘要。
- `--log-lines <n>` 控制每个日志来源最多返回多少行。
- `--save-local --yes` 会写入本地 `{appDir}/{serviceName}/{serviceVersion}`，必须显式传入 `--service-name`、`--service-version`、`--route-file-name`；它支持 XML、`common.config.properties`、`service.config.properties`、`.ds` 和三个受管固定 Schema，校验真实路径/符号链接边界并通过同目录临时文件原子替换，不主动 deploy/reload。
- `ai route apply --save-remote --yes` 从本地 XML 和重复 `--resource-file` 调用服务端 apply API，仅在用户明确授权远程写入时使用。`--resource-file` 只写不含目录的文件名时，相对 `--file` 指定的 route XML 所在目录解析；绝对路径和包含目录的相对路径保持按原路径解析。远程 apply 必须提供 `common.config.properties` 与 `service.config.properties`，`.ds` 等资源仅在 route XML 引用时必须提供。JSON 资源只接受 `request-schema.json`、`response-schema.json`、`callback-schema.json`，且必须与 JSON Schema 校验块或 Action input/output schema route property 的引用一一对应；`--timeout <seconds>` 传给服务端等待热加载。本地直编与受管 apply 是两条独立流程：同一次变更只选一条，live 文件修改后不用旧 session 或普通 apply 追认。
- `--action-session-id` 与 `--expected-scope-digest` 必须成对且只用于 `--save-remote`，此时调用 Action 会话受管入口，不允许 `--return-logs/--log-lines`。scope digest 从最新 session JSON 读取；冲突、STALE、transition unavailable 或恢复失败不得回退普通 apply。
- 远程 apply 返回 `FAILED`、`FAILED_ROLLED_BACK` 或 `ROLLBACK_FAILED` 时，CLI 先输出 `operationId`、删除文件、恢复状态和日志，再以退出码 `69` 结束。保留本地候选，不自动重试。
- `ai route apply --save-local --yes` 从本地 XML 和重复 `--resource-file` 写入服务目录；写入前把已有服务目录备份到 app 目录同级 `{appDirName}-backups`，拒绝备份源符号链接，可选 `--wait-reload --timeout <seconds>` 只读轮询路由详情。
- `--save-local` 与 `--save-remote` 互斥；本地保存是脚本和非 Codex 本地开发入口，不是 Codex 直接编辑服务文件的必经流程。
- `ai route optimize` 不接入 SSE。
- 模型 provider、base URL、model name、API key 都由服务端 `lightesb.ai.models.*` 注册表和 `lightesb.ai.agents.*.model-ref` 管理；不要写入 CLI profile。AI 路由生成/微调使用 `lightesb.ai.agents.route.model-ref`；Agent + Tools POC 使用 `lightesb.ai.agents.chat.model-ref`，推荐指向 DashScope `qwen-plus` 或 OpenAI-compatible Chat Completions 这类支持工具调用的模型。
- AI 路由可通过服务端 `provider=openai-responses` 接入 OpenAI 原生 Responses API，也可通过 `provider=custom` 和 `custom.api-type=chat-completions|responses` 接入自定义网关。`provider=openai` 不作为新配置入口。Responses provider 当前用于 AI 路由生成/微调和普通文本调用，不作为 Agent tool-calling 验收模型；Agent + Tools 应配置 `lightesb.ai.agents.chat.model-ref` 指向 Chat Completions 模型。服务管理前端会用 `aiRouteSessionId` 让支持 Responses 的 provider 在生成、微调和热部署失败修复之间续接模型上下文；CLI JSON 如需复用同一闭环，也可在 generate/optimize/apply 请求体中传同一个 `aiRouteSessionId`。首次业务 `CONTINUE` 如果本地还没有 previous response id，服务端也会作为 stateful 请求保存 provider response id；后续同 session 请求才携带 `previous_response_id`。若目标网关不支持 HTTP Responses `previous_response_id`，服务端会降级为无 session 调用。真实 provider 的 Responses 续接验证只能通过源码仓库显式 Maven profile 触发，交付包 CLI 默认命令不调用真实模型验证。

机器人边界：

- `robot doctor --offline` 可作为机器人样例包、配置、route、白名单和 processor 注册的静态门禁。
- `robot list/get/capabilities/state/audit` 只做管理 API 只读查询。
- `robot command validate --file` 只做服务端 validate-only 预检；请求体中的动态协议目标字段仍由服务端拒绝。
- `robot command status --robot-id --command-id` 只查已有命令结果，不提交新命令。
- `robot command submit --file --yes` 只提交到服务端命令账本、审计和 MQTT outbox；不直连协议端点，不证明真实执行成功。
- `robot inference decision-status` 只读；`robot inference submit` 必须 `--yes` 且只能消费已由验签 provider 批准的 decision。
- `robot command ingest-receipt --receipt-type ack|result --topic --payload-file|--payload-json --yes` 只把已捕获的 MQTT ack/result 回执转交服务端 ingest API；不订阅 MQTT，不派发命令。
- 当前 CLI 不提供 `move_to`、OPC UA write、Modbus write 或 rosbridge action 直连调用。
- 后续如需真实协议执行，必须另开真实协议闭环切片，不能把 `accepted` 当作执行成功。
- 默认自动化验证只要求本机 WSL 可运行 Maven；使用 mock HTTP 和本地单元测试，不要求真实地址或真实机器人环境。
- 真实机器人、broker、rosbridge、OPC UA、Modbus、Kafka 连通性必须通过显式联调脚本或现场测试验证。

## 最小接入链路

```bash
lightesb profile add --name dev --server http://localhost:8080
lightesb profile use dev
lightesb doctor
lightesb app create --file app.json --yes
lightesb message create --file request-message.json --yes
lightesb message create --file response-message.json --yes
lightesb service create --file service.json --yes
lightesb service config preview --file service.json
lightesb service config save --file service.json --yes
lightesb message schema generate --id <requestMessageId> --service-name DemoSrv --service-version v1.0.0 --schema-file request-schema.json --yes --output json
lightesb service package build --file package.json --yes
lightesb service package deploy --file package.json --yes
lightesb route status
lightesb log instance list --service-name DemoSrv --service-version 1.0.0
```

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `64` | 命令参数或确认缺失 |
| `65` | 输入文件或业务字段错误 |
| `69` | HTTP 或服务端错误 |
| `70` | CLI 软件错误 |
| `74` | IO 或网络请求错误 |
| `78` | 配置错误或 doctor 检查失败 |

## 写操作确认

以下命令默认要求 `--yes`：

```text
app create/update/delete
message create/update/delete/schema generate
service create/update/delete/export/config save/package build/package deploy/import/sync-remote/start/stop
deploy upload
ai route apply
ai route prepare
route reload-service/reload-file/unload
log level set/cleanup
keyword add/delete
```

HTTP 错误摘要会保留 status、错误码和可行动信息，并脱敏 token、password、secret、authorization、apiKey 等常见凭据。
