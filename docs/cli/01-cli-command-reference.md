# CLI 命令压缩参考

## 定位

远程排障用`--server http://目标IP:管理端口`或profile切换目标；snapshot由服务端读取自己的日志，无需共享磁盘或SSH。需网络可达和环境要求的身份权限，目标服务端必须包含所调用的API；旧版本返回404不代表没有故障日志。

服务create/update至少需要serviceName、serviceVersion（建议vX.Y.Z）、serviceImpl（例如REST）、serviceStatus（例如DEFINE）、serviceCall（例如SYNC）、serviceProvider（应用clientId）及serviceInId/serviceInRevision/serviceInModelDigest；SYNC还必须有serviceOutId/serviceOutRevision/serviceOutModelDigest。update还要求id和expectedDefinitionRevision。应用/消息/回调服务标识取真实查询结果，不能把provider当应用记录ID。

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
| `--ai-token <token>` | 兼容字段，以 `X-AI-Token` 发送；不恢复已移除的日志问答 |

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

应用探测通过POST pageVO读取1条记录；这是只读查询。doctor同时检查本地目录，纯CLI候选目录缺repo/app目录时须逐项查看结果，不把本地缺文件当作远程API不可用。

`diagnostics snapshot/warnings` 只调用：

```text
GET /api/diagnostics/runtime-snapshot
```

可选过滤参数为 `serviceName`、`serviceVersion` 和 `component`。当前组件包括 `route-runtime`、`service-log`、`external-datasource`、`robot-command`、`instance-log`。该命令面向 Codex 和人工远程排查；不读取远程文件系统，不触发重载、清理、关闭连接或日志级别调整。`--output json` 会保留服务端标准响应，包含 `requestId`、`components` 和服务端生成的 `warnings`。

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

### 注册系统与注册服务的查询口径

| 用户问法 | 查询命令 | 数据来源与名称字段 |
| --- | --- | --- |
| 目前有几个系统注册了、注册系统数量、接入系统/应用列表 | `app list --output json` | `ESBMCP_APP_MANAGE`，`APP_NAME`（返回 `appName`） |
| 注册了多少服务、服务数量、服务列表 | `service list --output json` | `ESBMCP_SERVICE_MANAGEMENT`，`SERVICE_NAME`（返回 `serviceName`） |

“系统注册”明确指接入应用，不能改查服务表或用服务数回答。一个系统可以提供多个服务；服务目录数、运行中的路由数、服务提供者列表均不能代替注册系统数。

只问数量时，用对应 list 命令的 `--page-num 1 --page-size 1 --output json`，读取成功响应的 `data.total`，不要用当前页 `data.records.length`。问全部数量时不加名称、提供者等过滤条件；用户指定过滤范围时，答案保留该范围。系统名称取 `data.records[].appName`，完整列表须继续分页。不要按名称去重后替代注册记录总数。查询失败或 `total` 缺失时说明无法确认，不能改查另一类对象或沿用历史数量。

```bash
# 注册系统数量；名称字段为 appName
lightesb app list --page-num 1 --page-size 1 --output json
# 注册服务数量
lightesb service list --page-num 1 --page-size 1 --output json
```

以上命令分别通过 `POST /app-manage/v1/pageVO` 和 `POST /service-management/v1/pageVO` 只读查询。表名用于解释业务口径，日常查询优先通过 CLI/管理 API，不需要直连数据库。回答分别使用“当前共注册了 N 个系统”和“当前共注册了 M 个服务”；同问两者时分别查询、分别报告。

### 建模命令

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
lightesb message schema generate --id <messageId> --revision <revisionId> --expected-model-digest <modelDigest> --service-name DemoSrv --service-version v1.0.0 --schema-file request-schema.json --yes
lightesb message schema generate --file message.json --service-name DemoSrv --service-version v1.0.0 --schema-file preview-schema.json --yes
lightesb message constraints
lightesb message domains
```


JSON 样例默认生成名为 `Request` 的 ROOT；`--msg-type RESPONSE` 将默认 ROOT 改为 `Response`。ROOT 节点的 `nodeName` 是生成 XML 时使用的实际根标签，可用 `--root-node-name <name>` 显式指定任意业务根名，且该输入优先于消息类型默认值。XML 样例保留自身根标签。模型恰好一个 ROOT，JSON/Schema 不增加 ROOT 名包装；alias 为 null/缺省才回退 nodeName，空串是精确 JSON 键。数组恰好一个任意类型 item。类型支持 ROOT/ENTRY/COLLECTION/VARCHAR2/REGEX/DATE/INT/NUMBER/BOOLEAN/NULL。defaultValue 是严格 JSON 值文本，null 字段表示未设置，文本 null/\"\"/0/false 区分显式 null/空串/数值/布尔；nullable 独立于必填。enumValues 用非空 JSON 数组文本，minimum/maximum 用精确数字文本。未知类型、无法表达的约束及无项证据的空数组明确拒绝。XML 属性、命名空间和混合文本暂不支持。

`message parse --output json`当前的`data`是JSON结构字符串，解析外层响应后再解析data，得到节点数组作为`msgStructure`。节点`fieldEscape`支持`ESCAPE`、`MIXED`；更新后用message get核对结构、alias、fieldEscape和新版本，不重复提交超时更新。

普通消息更新要求 `expectedRevision` 匹配当前修订；服务端在锁内从历史最高数值标签分配下一标签，编辑内容仍以当前修订为基线。标签为 `V{major}.{单数字minor}`，major 范围 0–2147483647 且无前导零；标签耗尽时拒绝更新。

消息影响分析可按`service list --page-num 1 --page-size 100 --output json`分页比较`serviceInId`/`serviceOutId`，直到完整读取data.total；回调消息引用使用当前服务的serviceCallbackMessageId固定快照，不读取目标当前输入代替。默认上限10请求/10页、10MiB、60秒；超预算、重复ID或分页变化报告不完整，不能声称无引用。使用provider/name过滤时结论仅适用于该范围。

`message schema generate` 从精确修订正式生成 Schema，或从文件预览：

- `POST /message-management/v1/json-schema/preview`
- `GET /message-management/v1/revisions/{id}/{revision}/json-schema`

`--id` 与 `--file` 必须且只能选一个。正式生成必须提供 `--revision` 和 `--expected-model-digest`，先核对服务固定绑定；三个固定文件自动推导方向，自定义正式文件另需 `--direction INPUT|OUTPUT|CALLBACK`。正式来源必须无 warnings；预览使用自定义文件名，不写正式来源。

`--app-dir` 默认是 `lightesb-camel-app`，目标版本目录必须存在。草稿目录已有 XML 时拒绝本地生成，请准备独立候选并受管 apply；冻结服务仅恢复已有受管文件相同 schemaDigest/generatorVersion。CLI 校验内容/对象/摘要一致后原样写入三个固定文件，并更新 service.config.properties 的 `lightesb.contract.<input|output|callback>.*` 八项来源：source=revision、message-name、msg-version、model-format-version、model-digest、snapshot-digest、generator-version、schema-digest。自定义正式文件不写受管前缀。

对象与权威文本中的数值按精确值比较，`10`、`10.0`、`1E+1` 等价；类型或精度差异、数组顺序变化仍拒绝。文件始终写入经过 SHA-256 校验的原始文本。

Schema 与 properties 分别原子替换；第二步失败会尝试恢复原 Schema，恢复不完整返回 IO 错误，先核对两文件。检测到链接或并发编辑时拒绝覆盖，不承诺两文件事务。`--yes` 必需，命令不部署/重载；JSON 返回实际 `data.file`、相对 `data.jsonSchemaPath`、Schema 内容/摘要、preview、版本及正式修订身份。

先用 `service list/get --output json` 读取固定三元组：INPUT 为 serviceInId/serviceInRevision/serviceInModelDigest，OUTPUT 为相应 serviceOut 字段；CALLBACK 为 serviceCallbackMessageId/serviceCallbackInRevision/serviceCallbackInModelDigest，serviceCallbackId 是服务 ID。首次受管文件暴露前冻结绑定、受管引用、模式和 Action 方向（保存/apply/部署等），后续失败不解冻，改变契约须新建服务版本。生成后保留 service.config.properties 来源；授权远程写入后随路由、两个 properties 和实际引用的 Schema 一次 apply。校验组连续设置 JsonSchemaPath、STRICT/LENIENT 并清除 JsonSchemaContent；不能用人工接受 warnings 绕过正式来源校验。

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
  "msgStructure": [
    {
      "nodeName": "Request",
      "nodeType": "ROOT",
      "nodeList": [
        {
          "nodeName": "orderId",
          "nodeDesc": "订单标识",
          "nodeType": "VARCHAR2",
          "nodeLength": "64",
          "ifRequired": "1",
          "nodeList": []
        }
      ]
    }
  ]
}
```

`msgStructure` 不能为空；最小创建样例也必须至少包含一个结构节点。

消息结构可同时记录内部节点名 `nodeName` 和外部字段别名 `alias`。内部节点名须为不带命名空间的合法 XML 标签名。可用 alias 显式指定 JSON 键，例如内部命名采用驼峰、外部字段为 `same_as_shipping` 时，可配置：

```json
{
  "nodeName": "sameAsShipping",
  "alias": "same_as_shipping",
  "nodeType": "VARCHAR2",
  "nodeList": []
}
```

生成 JSON Schema 和样例 JSON 时，alias 缺省或 null 才回退 nodeName，任何字符串（包括空串）都是精确 JSON 键。ROOT 与数组项不设置 alias；同级最终 JSON 键和 XML 节点名分别必须唯一。创建后建议执行 `message get --id <messageId> --output json` 做只读回查，不要只检查创建命令是否成功。

别名只负责字段命名映射，不改变类型。布尔使用 BOOLEAN；COLLECTION 恰好包含一个 item，可为标量、对象或嵌套数组，不为原始值数组增加对象包装。无法确定 item 的空数组和不兼容的混合类型样本明确拒绝。

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
lightesb deploy rollback <deploymentId> --yes --output json
lightesb deploy rollback <deploymentId> --no-auto-start --yes --output json
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
lightesb log snapshot --service-name DemoSrv --service-version v1.0.0 --lines 100 --output json
lightesb log services
lightesb log level set --service-key DemoSrv@1.0.0 --level DEBUG --yes
lightesb log cleanup --yes
lightesb log cleanup --manual --yes
lightesb log instance list --service-name DemoSrv --service-version v1.0.0
lightesb log instance list --service-name DemoSrv --service-version v1.0.0 --keyword patientId=10001
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
`log instance list --service-version` 使用精确服务版本目录名 `vX.Y.Z`，例如 `v1.0.0`；缺少 `v` 时 CLI 返回输入错误且不发送请求。

`deploy history` 默认返回最近 50 条部署记录，可用 `--service-name` 和 `--service-version` 过滤单个服务版本。列表输出只包含概要，不拉取完整部署步骤日志。

`log snapshot`作为基础只读排障能力直接提供。仅读取指定服务版本logs目录的最近片段，不开启DEBUG或改变级别；最多扫描128项、读取8个文件，每文件64KiB和1–200行。检查filesTruncated、truncated、changedDuringRead、readError；空/隐藏/变化/失败片段不能解释为“无异常”。依赖文件系统安全目录句柄，不支持时返回不可用，不退回不安全读取；不接受任意path，不承诺完整时间窗口或连续增量。

### Windows 服务端手工查看日志

当前暂不实现 Windows 服务端的 `log snapshot` 安全文件读取支持；不支持安全目录句柄时返回 HTTP `409 LOG_SNAPSHOT_UNAVAILABLE`，不会降级为不安全读取。这是服务端限制，与运行 CLI 的电脑是否为 Windows 无关。

请有文件访问权限的现场人员在 **LightESB 服务端机器** 上，进入实际服务根目录，直接查看对应服务版本的日志。默认位置为：

- DEBUG 日志：`lightesb-camel-app/{serviceName}/{serviceVersion}/logs/DEBUG.log`。
- 服务日志目录：`lightesb-camel-app/{serviceName}/{serviceVersion}/logs/`，查看其中已有的日志文件。

例如，Windows 下可在 PowerShell 中读取最近 100 行（将安装路径和服务身份替换为现场值）：

```powershell
Get-Content -LiteralPath 'D:\LightESB\lightesb-camel-app\DemoSrv\v1.0.0\logs\DEBUG.log' -Encoding UTF8 -Tail 100
```

目录名是 `logs`，`DEBUG.log` 默认位于该目录内，并非版本目录根下。若现场调整了服务根目录或日志输出路径，以实际配置为准。`DEBUG.log` 需要已开启该服务版本的 DEBUG 且有日志产生；文件不存在不能解释为没有故障，也不要为取证自动开启 DEBUG 或调整日志级别。手工读取的原始日志不经过快照接口脱敏，对外提供前须脱敏。


`deploy rollback <deploymentId> --yes` 恢复指定部署发生前的备份，必须先确认目标与授权。成功JSON保留新deploymentId、sourceDeploymentId及ROLLED_BACK；随后按新ID查询并核对服务/路由状态。`--no-auto-start`只跳过主动加载，Watcher仍可能处理恢复配置，不保证停服。无备份、冲突和失败均停止；默认30秒请求超时不表示服务端取消或未执行，先查history/status，不能自动重放回滚，归属不明时报告未知。

回滚失败的JSON保留脱敏`error.details`：可用时按`rollbackDeploymentId`查询新回滚记录，`deploymentId`为源记录ID；缺失时不从错误文字猜测。

`service start/stop` 等待服务端确认 Camel 上下文真实启动或卸载。部署状态为 `UNDEPLOYED` 时，`service start` 返回 HTTP `409 SERVICE_NOT_DEPLOYED`，应先生成并保存部署路由。同方向并发请求共享一次转换；相反方向、加载失败或超时会返回 HTTP `409` 并使 CLI 非零退出。超时不回滚 `server.running`，自动化脚本应查询服务状态或运行时诊断后再决定后续动作。成功结果中的 `idempotent=true` 表示没有重复写配置，`transitionReused=true` 表示复用了同方向任务。详见 [服务启停 API](../service-runtime-management-api.md)。

CLI 对 `service start/stop` 使用 130 秒 HTTP 请求超时，以覆盖服务端允许的 120 秒最大转换等待时间并接收结构化失败详情；其他命令仍使用默认 30 秒请求超时。

服务同步包使用 manifest.schemaVersion=2.0，不接受旧格式。导出按服务 INPUT/OUTPUT/CALLBACK 保存的固定消息 revision 读取快照，不读取最新消息代替；回调目标必须在目标环境存在且固定输入快照匹配。只传业务定义，不复制源运行/冻结状态；目标生成本地消息/修订 ID。同名同标签同完整摘要复用，缺失修订仅补历史并保留已有 currentRevision，同标签不同摘要拒绝。新消息以包内同名最高数值标签建立当前入口。

包只包含恰好一个根 XML、必需的 service.config.properties、properties、.ds 和根目录三个固定 Schema；Schema 与来源随精确修订一起验证。日志目录及带自动生成标记的日志配置不传输，手写日志配置保留。资源最多128项、单项2MiB、合计16MiB，metadata最多16MiB；ZIP最多132项、40MiB压缩大小、34MiB总解压大小。路径、服务归属、链接、严格UTF-8和完整摘要均须通过校验；摘要不代表发行者签名。export写本地包须--yes，import/sync-remote远程写也须--yes。

import-plan保持零写，启动选项与import相同：默认计划自动启动，--no-start计划不主动启动。预检返回消息CREATE_MESSAGE/CREATE_REVISION/REUSE及文件DEPLOY/RESUME/SKIP_DEPLOY等动作。APP/SERVICE可返回排序的details.changedFields，只列顶层字段名；MESSAGE返回sourceRevision、revision、currentVersion。update-existing只允许应用/服务字段更新，不能覆盖消息历史或冻结契约。

默认skip-existing只在当前服务身份有匹配现目录的最近完成部署或成功回滚证明，且XML/服务配置仍存在时保持文件，SKIP_DEPLOY不证明文件与候选相同；单纯服务行存在或失败记录不足以跳过。已有文件没有完成证明时，显式overwrite-service-files仍须通过冻结与合并候选验证。需要更换消息契约时新建服务版本。

中断后保留原包，以相同更新/覆盖/启动选项执行import-plan和import；RESUME复用原deploymentId。不要重新导出不同内容、手工改目录或用rollback代替未完成同步恢复。身份、目录配置、绑定或文件状态偏离会拒绝；失败不解除冻结，也不表示元数据未提交。完成同步后服务部署状态与同步历史共同标记成功，后续可使用服务start/stop。

--no-start只跳过主动启动，不关闭已有目录监听；显式server.running=false保持停止态。逐文件原子替换不等于目录整体事务；不支持多个运行实例同时发布同一目录。完成同步的回滚只处理同步清单内资源，保留CSV、自定义JSON、日志等清单外文件；须先核对backupAvailable与目标身份，首次没有旧备份不能回退。

sync-remote --keep-package可保留中间包，--package-out指定位置；JSON模式路径提示写stderr，stdout只输出一份apply响应。检查HTTP/退出码之外，还须检查data.status与action：操作占用可能仍返回HTTP200、success=true、CONFLICT。失败不拼接旧plan；写入结果不明时先查询部署状态，再用同包预检决定恢复。


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
  "serviceVersion": "v1.0.0",
  "serviceImpl": "REST",
  "serviceStatus": "DEFINE",
  "serviceCall": "SYNC",
  "serviceProvider": "HIS",
  "serviceInId": "<requestMessageId>",
  "serviceInRevision": "<requestRevisionId>",
  "serviceInModelDigest": "<requestModelDigest>",
  "serviceOutId": "<responseMessageId>",
  "serviceOutRevision": "<responseRevisionId>",
  "serviceOutModelDigest": "<responseModelDigest>"
}
```

`service create/update` 必须显式提供消息 ID、不可变修订 ID 和模型摘要；消息的新修订不会自动替换服务绑定。输入方向必填，SYNC 的输出必填，其他调用方式的输出可选但整组提供。更新还需 `id`，并将 `service get` 返回的 `definitionRevision` 填入 `expectedDefinitionRevision`；收到 409 时重新读取并合并，不能自动用最新比较版本重试覆盖。

回调的 `serviceCallbackId` 指向服务。选择时同时提交目标 `serviceCallbackName`、`serviceCallbackVersion`、`serviceCallbackInRevision` 和 `serviceCallbackInModelDigest`，取自目标服务的固定输入。调用方详情返回固定 `serviceCallbackMessageId` 及上述快照；目标草稿变化后必须显式重新选择。冻结版本不能改身份或绑定；ONE_WAY 已有的可选输出不会自动清除。

`serviceName` 是服务英文名和服务目录标识，只能包含字母、数字、下划线和中划线；中文展示名请写入 `serviceCnname`。

`package.json` 最小字段：

```json
{
  "serviceName": "DemoSrv",
  "serviceVersion": "1.0.0",
  "autoStart": true
}
```

## 外部 Agent 与路由候选命令

```bash

lightesb ai route read --service-name DemoAiSrv --service-version 1.0.0
lightesb ai route prepare --service-name DemoAiSrv --service-version v1.0.0 --out build/DemoAiSrv-v1.0.0-candidate --yes --output json
lightesb ai route validate --file build/DemoAiSrv-v1.0.0-candidate/DemoAiSrv-ai-route.xml --service-name DemoAiSrv --service-version v1.0.0 --route-file-name DemoAiSrv-ai-route.xml --resource-file common.config.properties --resource-file service.config.properties,input-transform.ds,request-schema.json --output json
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

- 内置 `log ask` 已移除，调用返回参数错误且不发送请求；旧 `/api/ai/logging/chat` 返回 404。外部 Agent 使用 `log snapshot`、`log instance` 等命令采集证据，日志写操作仍需独立授权及 `--yes`。
- `ai diagnose` 只检查 server、日志健康与可选路由内容，不调用模型或检查模型密钥。
- 内置 `ai route generate/optimize/latest/cache` 及旧 `ai tool list/save/plan/run` 已移除，调用返回参数错误且不发送请求；旧生成、微调、SSE、latest 和缓存 HTTP 接口返回 404。停止旧轮询，改由外部 Agent 编辑候选，再使用 read/prepare/validate/apply。
- `ai route prepare --out <new-candidate-dir> --yes` 只调用在线 content GET，把实际 route、两个 properties、route 实际引用的 `.ds` 和固定 Schema 作为整体发布到新本地目录。父目录必须真实存在，`--out` 必须不存在；命令拒绝 symlink 和当前工作目录下默认 `lightesb-camel-app`，但无法自动发现自定义或远程 Watcher 根。content/prepare 不证明服务已注册、路由已加载或 Action Catalog 与持久化目录一致。
- `ai route validate` 只调用候选校验 API，不需要 `--yes`，不写本地/远程文件、不热加载、不建立审批 lineage。裸 `--resource-file` 文件名相对 `--file` 所在候选目录解析；成功响应的 `savedFiles/deletedFiles` 用于确定随后会话的精确文件 allowlist。
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

外部 Agent 的模型配置与凭据由其自身环境维护，不写入 CLI profile 或服务文件。`aiRouteSessionId` 模型字段已移除，Action 审批会话和管理认证保持原契约。

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

以下使用已授权的远程 apply 发布新服务。先准备 app.json、request-message.json、response-message.json；每步读取返回的真实 ID，创建消息后用 message get 获取 currentRevision/modelDigest，再填入 service.json。示例服务使用 SYNC，须绑定输入和输出；下例路由只引用输入 Schema，输出绑定不要求自动增加响应校验。

```bash
lightesb profile add --name dev --server http://localhost:8080
lightesb profile use dev
lightesb doctor
lightesb app create --file app.json --yes --output json
lightesb message create --file request-message.json --yes --output json
lightesb message create --file response-message.json --yes --output json
lightesb message get --id <requestMessageId> --output json
lightesb message get --id <responseMessageId> --output json
# 用上一步真实ID、不可变修订和摘要填写service.json
lightesb service create --file service.json --yes --output json
mkdir -p build/contract-candidate/DemoSrv/v1.0.0
lightesb service config preview --file service.json --output json > build/contract-candidate/config-preview.json
```

确认 build/contract-candidate 位于所有实际监听根之外。将预览 JSON 的 `data.commonConfig`、`data.serviceConfig` 字符串解码后，分别按 UTF-8 写入候选版本目录的 `common.config.properties`、`service.config.properties`，保留真实换行，不把 JSON 信封或转义后的字符串直接当作 properties。核对服务身份、业务端口及路由所需配置；此时版本目录中不要放 XML。

```bash
lightesb message schema generate --id <requestMessageId> --revision <requestRevisionId> --expected-model-digest <requestModelDigest> --app-dir build/contract-candidate --service-name DemoSrv --service-version v1.0.0 --schema-file request-schema.json --yes --output json
```

保留生成的 Schema 和 CLI 更新后的 service.config.properties。再将外部 Agent 准备并审核的 `DemoSrv-route.xml` 写入同一候选版本目录，配置连续的 JsonSchemaPath=request-schema.json、STRICT/LENIENT、清除 JsonSchemaContent 及校验 processor；不要让 Agent 自行生成或修改 Schema。如果 XML 引用其他资源，先在候选内补齐并在以下两个命令同时列出。

```bash
lightesb ai route validate --file build/contract-candidate/DemoSrv/v1.0.0/DemoSrv-route.xml --service-name DemoSrv --service-version v1.0.0 --route-file-name DemoSrv-route.xml --resource-file common.config.properties --resource-file service.config.properties --resource-file request-schema.json --output json
# 确认校验结果与授权范围后，一次提交同一候选
lightesb ai route apply --file build/contract-candidate/DemoSrv/v1.0.0/DemoSrv-route.xml --service-name DemoSrv --service-version v1.0.0 --route-file-name DemoSrv-route.xml --resource-file common.config.properties --resource-file service.config.properties --resource-file request-schema.json --save-remote --yes --output json
lightesb route status
lightesb log instance list --service-name DemoSrv --service-version v1.0.0
```

按 apply 的业务状态及目标路由实际响应验收；需要审批 lineage 的场景另按会话流程准备精确 allowlist 和 scope digest。包构建/部署是另一路发布入口，不在本例 apply 后重复部署。

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
deploy upload/rollback
ai route apply
ai route prepare
route reload-service/reload-file/unload
log level set/cleanup
keyword add/delete
```

HTTP 错误摘要会保留 status、错误码和可行动信息，并脱敏 token、password、secret、authorization、apiKey 等常见凭据。

## 业务 Action 固定快照样例

订单、ERP/WMS 对账、回款异常见 [业务演示说明](../manufacturing-action-demo.md)。查询使用配置的 profile；显式 `--server` 会切换为不携带 profile bearer 的连接，受保护的 Action 查询应使用正确 profile。`get` 只返回 Schema 路径/摘要，需核对随包正文；有 HTTP 下游的 read Action 仍需已批准 sessionId。

### JSON 错误与自动化

`--output json` 下CLI错误输出为单个 `success=false` 对象，含 `exitCode`、`error.category`、`error.code`、安全 `message` 和 `outcome=UNKNOWN`；服务端提供时另有 `httpStatus`、`serverCode` 和 `requestId`。默认文本模式与退出码保持，缺 `--yes` 仍返回64。无效output格式使用文本usage提示。自动化不解析stderr自然语言，也不因网络错误认定写入未发生；先按已知操作ID查询，不能自动重放写入。查询成功但业务对象状态FAILED与命令执行失败要分开判断。

## 消息修订更新与精确读取

更新前用 `message get --id <messageId> --output json` 读取详情，把 `data.currentRevision` 原样填入更新 JSON 的 `expectedRevision`，同时填写消息 `id`。`message update --file message.json --yes` 缺少期望修订会失败；HTTP 409 / `MESSAGE_REVISION_CONFLICT` 表示已被修改，须重新读取、核对并合并修改，禁止自动替换修订号重试覆盖。消息名称在删除后仍占用。

`message get --id <messageId> --revision <revisionId>` 读取不可变历史快照，revisionId 可从详情 `versionList[].revision` 获得。历史响应 `id` 为修订 ID，`msgId` 为消息 ID；展示标签 `msgVersion` 不能代替 revisionId。精确读取不自动跟随最新版本。使用前用当前包 `message get --help` 核对命令支持。
