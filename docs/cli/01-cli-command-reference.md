# CLI 命令压缩参考

## 定位

CLI 只调用 LightESB 控制面 API 和本地配置，不承载 Camel 运行时，不直接读写 `lightesb-camel-app/` 服务目录，不绕过服务端状态机。

## 安装与入口

```bash
java -jar lightesb-cli.jar --help
java -jar lightesb-cli.jar --version
alias lightesb='java -jar /path/to/lightesb-cli.jar'
```

## 全局参数

| 参数 | 说明 |
| --- | --- |
| `--server http://host:port` | 单次命令指定服务端 |
| `--profile <name>` | 使用本地 profile |
| `--output table|json` | 输出格式，CI 优先 `json` |
| `--yes` | 写操作确认 |
| `--file payload.json` | 从 JSON 文件读取输入 |
| `--ai-token <token>` | 用于服务端 AI 日志问答等 AI 管控接口的 `X-AI-Token` |

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
lightesb robot command ingest-receipt --receipt-type ack --topic robot/site-a/quad-001/command/cmd-001/ack --payload-file ack.json --yes
lightesb robot command ingest-receipt --receipt-type result --topic robot/site-a/quad-001/command/cmd-001/result --payload-json '{"commandId":"cmd-001","robotId":"quad-001","siteId":"site-a","status":"succeeded"}' --yes --output json
lightesb diagnostics snapshot
lightesb diagnostics snapshot --component route-runtime --output json
lightesb diagnostics snapshot --service-name DemoSrv --service-version v1.0.0 --output json
lightesb diagnostics warnings
lightesb diagnostics warnings --component service-log --output json
```

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
lightesb robot policy disable --server http://localhost:8080 --id <policyId> --yes
```

这些命令只调用 `GET/POST /service-management/v1/robots/policies/denylist` 及 `POST /service-management/v1/robots/policies/denylist/{id}:disable`。命中启用策略时，`commands:validate` 和 `commands` 返回 `ROBOT_POLICY_REJECTED`，不会触发协议调用。

当前默认用本机 WSL mock HTTP 和本地测试验证，不证明真实资产库、真实在线状态、真实审计源、真实协议执行状态或真实能力发现。

`robot command validate --file` 从 JSON 文件读取 `robotId`，只调用：

```text
POST /service-management/v1/robots/{robotId}/commands:validate
```

它用于命令预检，不调用 `/commands`，不创建命令记录，不连接 MQTT、rosbridge、OPC UA、Modbus、Kafka、WMS/MES，也不写执行审计。`--output json` 保留服务端标准响应。

`robot command status --robot-id --command-id` 只查询已有命令结果，不调用 `POST /commands`，不创建新命令。`--output json` 保留服务端标准响应。

`robot command submit --file --yes` 只调用：

```text
POST /service-management/v1/robots/{robotId}/commands
```

它会提交到服务端命令入口，必须显式传 `--yes`，并拒绝 `mode=validate_only` 和 `dryRun=true`。服务端返回 `protocolReceipt.outboxStatus=pending` 时，只表示命令已进入可靠派发队列；`protocolReceipt.dispatched=false` 不能当作机器人已收到或已执行。

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
lightesb message parse --file sample.xml
lightesb message constraints
lightesb message domains
```

后端已提供消息体 JSON Schema 预览接口：

- `POST /message-management/v1/json-schema/preview`
- `GET /message-management/v1/json-schema/preview/{id}`

当前 CLI 尚未封装独立命令；自动化场景可通过通用 HTTP 调用控制面接口。

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
  "msgStructureJson": "{}",
  "msgStructure": []
}
```

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
lightesb service package build --file package.json
lightesb service package deploy --file package.json --yes
lightesb service start --id <serviceId> --yes
lightesb service stop --id <serviceId> --yes
lightesb service export --local-server http://localhost:8080 --app-dir lightesb-camel-app --service-name DemoSrv --service-version v1.0.0 --out dist/DemoSrv-v1.0.0.lightesb-service.zip
lightesb service import-plan --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip
lightesb service import --server http://remote-host:8080 --file dist/DemoSrv-v1.0.0.lightesb-service.zip --skip-existing --yes
lightesb service sync-remote --server http://remote-host:8080 --local-server http://localhost:8080 --app-dir lightesb-camel-app --service-name DemoSrv --service-version v1.0.0 --keep-package --yes

lightesb deploy validate ./DemoSrv.zip
lightesb deploy upload ./DemoSrv.zip
lightesb deploy upload ./DemoSrv.zip --target-directory /opt/lightesb/services --no-auto-start
lightesb deploy status <deploymentId>
lightesb deploy history --limit 20
lightesb deploy history --service-name DemoSrv --service-version 1.0.0 --limit 20

lightesb route info
lightesb route status
lightesb route mapping
lightesb route detail --file-key <fileKey>
lightesb route config --file-key <fileKey>
lightesb route reload-service --service-name DemoSrv --service-version 1.0.0 --yes
lightesb route reload-file --file-path /path/on/server/route.xml --yes
lightesb route unload --file-path /path/on/server/route.xml --yes

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

`deploy history` 默认返回最近 50 条部署记录，可用 `--service-name` 和 `--service-version` 过滤单个服务版本。列表输出只包含概要，不拉取完整部署步骤日志。

服务同步命令用于把本地服务版本迁移到远端 LightESB。导出包包含服务定义、接入系统、报文模型和服务目录文件，并在 manifest 中记录 metadata 与服务文件 `sha256`。`serviceVersion` 必须使用 `vX.Y.Z`。`import-plan` 只读远端状态；写入命令必须加 `--yes`。`--skip-existing` 是默认幂等策略的显式写法。远端已有同名服务版本时默认跳过服务文件部署；需要覆盖时加 `--overwrite-service-files`。默认部署后自动启动路由；需要关闭时加 `--no-start`。`sync-remote --keep-package` 可保留中间导出包，也可用 `--package-out <path>` 指定路径。接入系统或服务定义冲突默认失败；需要更新时加 `--update-existing`。远端已有同名报文且内容不一致时会调用消息更新接口，远端当前 `msgVersion` 必须是 `V数字.单数字`，更新后递增单数字小版本并保留更新历史，例如 `V1.9` -> `V2.0`。

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
lightesb ai route cache status
lightesb ai route cache clear --yes
lightesb ai route cache clear --service-name DemoAiSrv --service-version v1.0.0 --yes
lightesb ai route optimize --file ai-route-chat.json
lightesb ai route optimize --file ai-route-chat.json --save-remote --return-logs --log-lines 80 --yes
lightesb ai route optimize --file ai-route-chat.json --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --yes
lightesb ai route apply --file route.xml --save-remote --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --resource-file input-transform.ds --resource-file output-transform.ds --return-logs --log-lines 80 --timeout 30 --yes
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
- `ai route cache status` 查询服务端 AI 路由上下文选择、baseline 和最近生成结果缓存状态。
- `ai route cache clear --yes` 清理服务端 AI 路由缓存；带 `--service-name` 与 `--service-version` 时只清理指定服务关联缓存。
- `--save-remote --yes` 会调用服务端 `/service-management/v1/ai/route/apply`，由服务端备份、写入、等待 XML/properties 热加载并返回状态；CLI 不通过 SSH/SCP 或共享磁盘写远程文件。
- `--return-logs` 控制成功时是否返回远程日志摘要；失败时即使未传 `--return-logs`，也会展示服务端返回的多个日志来源摘要。
- `--log-lines <n>` 控制每个日志来源最多返回多少行。
- `--save-local --yes` 会写入本地 `{appDir}/{serviceName}/{serviceVersion}`，必须显式传入 `--service-name`、`--service-version`、`--route-file-name`；它支持 XML、`common.config.properties`、`service.config.properties` 和 `.ds` 资源文件，不主动 deploy/reload。
- `ai route apply --save-remote --yes` 从本地 XML 和重复 `--resource-file` 调用服务端 apply API；远程 apply 必须提供 `common.config.properties` 与 `service.config.properties`，`.ds` 等资源仅在 route XML 引用时必须提供；`--timeout <seconds>` 传给服务端等待热加载。
- `ai route apply --save-local --yes` 从本地 XML 和重复 `--resource-file` 写入服务目录；写入前把已有服务目录备份到 app 目录同级 `{appDirName}-backups`，可选 `--wait-reload --timeout <seconds>` 只读轮询路由详情。
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
lightesb service package build --file package.json
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
message create/update/delete
service create/update/delete/config save/package deploy/start/stop
route reload-service/reload-file/unload
log level set/cleanup
keyword add/delete
```

`deploy upload` 当前示例不强制 `--yes`，但流水线侧应自行增加确认门禁。
