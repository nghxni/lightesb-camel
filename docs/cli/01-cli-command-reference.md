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
| `--ai-token <token>` | 用于服务端 AI 日志问答和 AI 工具接口的 `X-AI-Token` |

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
```

`doctor` 只做环境和只读 API 检查，不修改服务端状态。

`robot doctor --offline` 只做机器人接入静态检查，输出 PASS/WARN/FAIL 和 `connectivityChecked=false`；不连接真实 endpoint，不下发机器人命令，不调用验证 route。

在线 `robot doctor` 当前不启用。真实资产库、最近心跳/遥测数据源、结构化错误日志或日志检索 API、只读权限和站点隔离稳定前，不能把 offline 输出解释为真实资产在线、最近心跳健康或现场错误日志已检查。

`robot list/get/capabilities/state/audit` 只调用：

```text
GET /service-management/v1/robots
GET /service-management/v1/robots/{robotId}
GET /service-management/v1/robots/{robotId}/capabilities
GET /service-management/v1/robots/{robotId}/state
GET /service-management/v1/robots/{robotId}/audit
GET /service-management/v1/robots/{robotId}/commands/{commandId}
```

这些命令是只读查询，不提交动作，不清理审计数据，不连接真实协议 endpoint。当前默认用本机 WSL mock HTTP 和本地测试验证，不证明真实资产库、真实在线状态、真实审计源、真实协议执行状态或真实能力发现。

`robot command validate --file` 从 JSON 文件读取 `robotId`，只调用：

```text
POST /service-management/v1/robots/{robotId}/commands:validate
```

它用于命令预检，不调用 `/commands`，不创建命令记录，不连接 MQTT、rosbridge、OPC UA、Modbus、Kafka、WMS/MES，也不写执行审计。`--output json` 保留服务端标准响应。

`robot command status --robot-id --command-id` 只查询已有本地命令结果，不调用 `POST /commands`，不创建新命令。`--output json` 保留服务端标准响应。

`robot command submit --file --yes` 只调用：

```text
POST /service-management/v1/robots/{robotId}/commands
```

它会提交到本地命令持久化入口，必须显式传 `--yes`，并拒绝 `mode=validate_only` 和 `dryRun=true`。服务端返回 `protocolReceipt.dispatched=false` 时，只表示管理 API 已本地 accepted，不能当作真实机器人命令下发入口。

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
```

`deploy history` 默认返回最近 50 条部署记录，可用 `--service-name` 和 `--service-version` 过滤单个服务版本。列表输出只包含概要，不拉取完整部署步骤日志。

日志级别调整后立即生效，不需要执行日志重载。

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

lightesb ai tool list --service-id <serviceId>
lightesb ai tool list --service-id <serviceId> --output json
lightesb ai tool save --service-id <serviceId> --file tools.json --yes
lightesb ai tool plan --message "查询订单 MOCK-1001 的详情"
lightesb ai tool plan --message "查询订单 MOCK-1001 的详情" --memory-id cli-session-001 --output json
lightesb ai tool run --message "查询订单 MOCK-1001 的详情" --yes
lightesb ai tool run --plan-file plan-result.json --yes

lightesb ai route generate --file ai-route.json
lightesb ai route generate --file ai-route.json --save-remote --return-logs --log-lines 80 --yes
lightesb ai route generate --file ai-route.json --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --yes
lightesb ai route read --service-name DemoAiSrv --service-version 1.0.0
lightesb ai route optimize --file ai-route-chat.json
lightesb ai route optimize --file ai-route-chat.json --save-remote --return-logs --log-lines 80 --yes
lightesb ai route optimize --file ai-route-chat.json --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --yes
lightesb ai route apply --file route.xml --save-remote --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --resource-file input-transform.ds --return-logs --log-lines 80 --timeout 30 --yes
lightesb ai route apply --file route.xml --save-local --app-dir lightesb-camel-app --service-name DemoAiSrv --service-version 1.0.0 --route-file-name DemoAiSrv-ai-route.xml --resource-file input-transform.ds --yes
lightesb ai diagnose
lightesb ai diagnose --service-id SRV1 --service-name DemoAiSrv --service-version 1.0.0 --output json
```

AI 边界：

- `log ask` 是可选服务端自然语言 Agent 能力，只把问题、`memoryId` 和 `X-AI-Token` 传给服务端，不在 CLI 本地推理日志语义；默认日志治理优先使用确定性 `log` 命令。
- `ai tool plan/run` 只调用服务端 AI 工具接口，不在 CLI 本地查库或调用工具 URL。
- `ai tool run` 初版要求 `--yes`；CI 使用 `--output json` 保存 `plan` 结果，再用 `run --plan-file` 执行。
- `ai route generate` / `ai route optimize` 默认只返回候选 XML，不写入 `lightesb-camel-app`，不保存配置，不自动部署。
- `--save-remote --yes` 会调用服务端 `/service-management/v1/ai/route/apply`，由服务端备份、写入、等待 XML/properties 热加载并返回状态；CLI 不通过 SSH/SCP 或共享磁盘写远程文件。
- `--return-logs` 控制成功时是否返回远程日志摘要；失败时即使未传 `--return-logs`，也会展示服务端返回的多个日志来源摘要。
- `--log-lines <n>` 控制每个日志来源最多返回多少行。
- `--save-local --yes` 会写入本地 `{appDir}/{serviceName}/{serviceVersion}`，必须显式传入 `--service-name`、`--service-version`、`--route-file-name`；它支持 XML、`common.config.properties`、`service.config.properties` 和 `.ds` 资源文件，不主动 deploy/reload。
- `ai route apply --save-remote --yes` 从本地 XML 和重复 `--resource-file` 调用服务端 apply API；`--timeout <seconds>` 传给服务端等待热加载。
- `ai route apply --save-local --yes` 从本地 XML 和重复 `--resource-file` 写入服务目录；写入前把已有服务目录备份到 app 目录同级 `{appDirName}-backups`，可选 `--wait-reload --timeout <seconds>` 只读轮询路由详情。
- `--save-local` 与 `--save-remote` 互斥；本地保存是脚本和非 Codex 本地开发入口，不是 Codex 直接编辑服务文件的必经流程。
- `ai route optimize` 不接入 SSE。
- 模型 provider、base URL、model name、API key 都由服务端配置管理；不要写入 CLI profile。

机器人边界：

- `robot doctor --offline` 可作为机器人样例包、配置、route、白名单和 processor 注册的静态门禁。
- `robot list/get/capabilities/state/audit` 只做管理 API 只读查询。
- `robot command validate --file` 只做服务端 validate-only 预检；请求体中的动态协议目标字段仍由服务端拒绝。
- `robot command status --robot-id --command-id` 只查已有本地命令结果，不提交新命令。
- `robot command submit --file --yes` 只做本地持久化 accepted，不证明真实协议执行。
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
ai tool save/run
```

`deploy upload` 当前示例不强制 `--yes`，但流水线侧应自行增加确认门禁。
