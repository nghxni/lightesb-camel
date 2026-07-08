# 机器人命令 dispatcher API

本文说明交付包中机器人命令提交、MQTT outbox 和状态查询边界。

## 提交命令

```bash
curl -sS -X POST http://127.0.0.1:8080/service-management/v1/robots/quad-001/commands \
  -H "Content-Type: application/json" \
  -d '{"commandId":"cmd-001","robotId":"quad-001","siteId":"site-a","commandType":"move_to","mode":"submit","timeoutMs":30000,"target":{"frame":"map","x":1.2,"y":3.4}}'
```

成功后服务端写入命令账本、审计和 MQTT outbox。响应中的 `status=accepted` 与 `protocolReceipt.outboxStatus=pending` 只表示命令已进入可靠派发队列。

示例响应：

```json
{
  "success": true,
  "data": {
    "commandId": "cmd-001",
    "robotId": "quad-001",
    "status": "accepted",
    "protocolReceipt": {
      "protocol": "mqtt5",
      "dispatched": false,
      "outboxStatus": "pending",
      "topic": "robot/site-a/quad-001/command/cmd-001"
    }
  },
  "error": null,
  "timestamp": 1782817800000,
  "requestId": "REQ-..."
}
```

## 查询

```bash
curl -sS http://127.0.0.1:8080/service-management/v1/robots/quad-001/commands/cmd-001
curl -sS http://127.0.0.1:8080/service-management/v1/robots/quad-001/audit?commandId=cmd-001
curl -sS -X POST http://127.0.0.1:8080/service-management/v1/robots/commands:dispatch-next
```

`GET /commands/{commandId}` 只查询已有命令结果，不创建命令、不触发派发。

`GET /audit` 查询命令审计，支持 `commandId` 和 `eventType` 过滤。

`POST /commands:dispatch-next` 手动触发一次 dispatcher，从 outbox claim 一条到期 `pending` 记录并派发到 MQTT。成功后 outbox 变为 `dispatched`，命令状态推进到 `dispatched`，并追加 `robot.command.dispatched` 审计。该接口用于运维验证和手动补偿，不代表自动调度循环已经启用。

无 MySQL POC 可配置 `lightesb.poc.h2-fallback.enabled=true`，机器人命令账本、审计、outbox 和状态快照使用 H2 同名表。该模式只用于小数据量演示，不承诺生产级归档、保留、备份恢复或切回 MySQL 后的数据迁移。

## MQTT 回执接入基线

交付包已提供可被 MQTT consumer 复用的 ack/result 回执接入服务基线。当前自动化验证可使用 mock topic 和 JSON payload；也可在本机 EMQX 或强模拟器环境下，先由正式 dispatcher 派发 command，再把模拟固件捕获并发布的 ack/result 转交 ingest。该能力不新增默认真实 MQTT consumer route。

运行态 mock/local E2E 可调用：

```bash
curl -sS -X POST http://127.0.0.1:8080/service-management/v1/robots/mqtt-receipts:ingest \
  -H "Content-Type: application/json" \
  -d '{"receiptType":"ack","topic":"robot/site-a/quad-001/command/cmd-001/ack","payloadJson":"{\"commandId\":\"cmd-001\",\"robotId\":\"quad-001\",\"siteId\":\"site-a\",\"status\":\"accepted\",\"correlationId\":\"corr-cmd-001\"}"}'
```

请求字段：

| 字段 | 说明 |
| --- | --- |
| `receiptType` | `ack` 或 `result`，必须与 topic 后缀一致。 |
| `topic` | MQTT 回执 topic。 |
| `payloadJson` | MQTT 回执 payload 的 JSON 字符串。 |

回执 topic：

| 回执 | Topic |
| --- | --- |
| ack | `robot/{siteId}/{robotId}/command/{commandId}/ack` |
| result | `robot/{siteId}/{robotId}/command/{commandId}/result` |

payload 至少包含 `siteId`、`robotId`、`commandId` 和 `status`，并且 `siteId`、`robotId`、`commandId` 必须与 topic 一致。不一致、缺字段或非法 status 会返回 `ROBOT_MQTT_RECEIPT_INVALID`，不推进状态，也不写命令审计。

状态映射：

| 回执 | status | 状态推进 |
| --- | --- | --- |
| ack | `accepted` | `dispatched -> acknowledged` |
| ack | `rejected` | `dispatched -> failed` |
| result | `succeeded` | `dispatched|acknowledged -> succeeded` |
| result | `failed` | `dispatched|acknowledged -> failed` |
| result | `timeout` | `dispatched|acknowledged -> timeout` |
| result | `rejected` | 映射为 `failed`，原始拒绝语义保留在 payload 摘要中 |

result 可以早于 ack 到达：只要命令已 `dispatched`，result 可直接推进到 `succeeded`、`failed` 或 `timeout` 终态；后续迟到 ack 返回 ignored 语义，不回退状态。`timeout` 或 `failed` 后迟到的 `succeeded` 不允许覆盖终态。重复回执、终态后的迟到 ack 和乱序 result 不会重复写审计，也不会回退状态。审计写入失败时，状态推进和审计写入同事务回滚。

成功推进状态的 dispatcher、ack 和 result 会派生最新状态快照。`GET /service-management/v1/robots/{robotId}/state` 优先读取持久化快照；无快照时返回管理面样例快照并标记 `sourceType=management_snapshot`。快照字段包括 `onlineStatus`、`health`、`protocolProfile`、`lastTelemetryAt`、`lastCommandId`、`lastErrorCode`、`sourceType` 和 `updatedAt`。第一版不开放状态 upsert API，也不代表真实遥测、真实在线心跳或现场位姿已经接入。

该 HTTP 入口用于 mock/local 和运行态 E2E 验证，不代表默认生产环境已启用真实 MQTT consumer。真实 MQTT consumer 仍需单独接入 broker 订阅、凭据、ACL、弱网和跨实例验证。

本机已有 EMQX 或强模拟器时，可用交付脚本验证正式 dispatcher 与回执入账闭环：

```bash
export LIGHTESB_BASE=http://127.0.0.1:8080
export ROBOT_MQTT_BROKER_URI=tcp://127.0.0.1:1883
tools/robot-mqtt-firmware-precheck/test_robot_mqtt_firmware_precheck.sh --dispatcher-ingest
```

通过标准是 `accepted -> dispatched -> acknowledged -> succeeded`，并能查询到 submitted、dispatched、ack、result 审计。该模式仍属于 local simulator 验证，不等同于现场机器人、ACL、弱网、离线会话或跨实例验收。

## 审计归档

`ROBOT_AUDIT_LOG` 默认由服务端自动归档，不需要 CLI 触发：

- 每天凌晨 1 点执行。
- 数据库审计默认保留 1 个月。
- SQL 备份默认保留 24 个月。
- 归档文件写入 `${lightesb.deployment.backup-dir}/audit`。
- 文件名格式为 `ROBOT_AUDIT_LOG-yyyyMMddHHmmss.sql`。
- 文件先写 `.tmp`，校验成功后改名为 `.sql`。
- 导出成功后只删除本次已导出的审计记录，不删除命令账本或 outbox。

可交付配置：

| 配置键 | 默认值 | 说明 |
| --- | --- | --- |
| `lightesb.robot.audit.archive.enabled` | `true` | 是否启用自动归档。 |
| `lightesb.robot.audit.archive.retention-months` | `1` | 数据库审计保留月数。 |
| `lightesb.robot.audit.archive.backup-retention-months` | `24` | SQL 备份文件保留月数。 |
| `lightesb.robot.audit.archive.max-field-chars` | `65536` | 单字段最大归档字符数，超过时任务失败且不删除数据库记录。 |

dispatcher 交付配置：

| 配置键 | 默认值 | 说明 |
| --- | --- | --- |
| `lightesb.robot.dispatcher.enabled` | `false` | 是否允许 dispatcher 派发 outbox。 |
| `lightesb.robot.dispatcher.broker-uri` | 空 | MQTT broker URI。 |
| `lightesb.robot.dispatcher.client-id` | `lightesb-robot-dispatcher` | MQTT clientId。 |
| `lightesb.robot.dispatcher.username` / `password` | 空 | MQTT 认证参数，建议通过环境变量注入。 |
| `lightesb.robot.dispatcher.qos` | `1` | MQTT QoS。 |
| `lightesb.robot.dispatcher.retained` | `false` | command 是否 retained，生产建议保持 `false`。 |
| `lightesb.robot.dispatcher.clean-start` | `true` | MQTT cleanStart。 |
| `lightesb.robot.dispatcher.session-expiry-interval` | `0` | MQTT sessionExpiryInterval。 |
| `lightesb.robot.dispatcher.command-topic-pattern` | `robot/{siteId}/{robotId}/command/{commandId}` | command topic 模板。 |

## 输入边界

必填字段：

| 字段 | 说明 |
| --- | --- |
| `commandId` | 业务幂等键。 |
| `siteId` | 站点 ID。 |
| `commandType` | 动作类型。 |
| `timeoutMs` | 超时时间，必须大于 0。 |
| `target` 或 `payload` | 至少一个。 |

禁止在请求体中传动态协议目标字段，例如 `topic`、`mqttTopic`、`node`、`register`、`service`、`broker`、`endpoint`、`unitId`、`functionCode`。

## 状态语义

| 状态 | 含义 |
| --- | --- |
| `accepted` | 管理 API 已接受并写入 outbox。 |
| `dispatched` | dispatcher 已完成协议派发。 |
| `acknowledged` | 已收到 ack。 |
| `succeeded` | 已收到成功 result。 |
| `failed` / `timeout` | 执行失败或超时。 |

## 错误码

| 场景 | HTTP | 错误码 |
| --- | --- | --- |
| 未知机器人 | 404 | `ROBOT_NOT_FOUND` |
| schema 缺失或模式错误 | 400 | `ROBOT_COMMAND_SCHEMA_INVALID` |
| 动态协议目标字段 | 422 | `ROBOT_POLICY_REJECTED` |
| 能力不支持 | 422 | `ROBOT_CAPABILITY_NOT_SUPPORTED` |
| commandId 重复但 payload 不同 | 409 | `ROBOT_COMMAND_DUPLICATE_CONFLICT` |
| MQTT 回执 topic/payload 不合法 | 400 | `ROBOT_MQTT_RECEIPT_INVALID` |

## 路由 mock 验证

不连接真实 MQTT broker 或机器人时，可以用 HTTP 路由包装机器人 processor 做 mock 验证：

1. `system.components=undertowhttp,robotics`。
2. HTTP 入口接收高层命令 JSON。
3. 路由内调用 `robotCommandValidateProcessor` 和 `robotCommandEnvelopeProcessor`。
4. 成功时返回 `accepted` 和由配置生成的 command topic。
5. 参数、能力或动态协议目标字段错误用局部 `doTry/doCatch` 返回 400/422。
6. 未预期异常再交给全局异常兜底。

示例拒绝分支：

```xml
<doTry>
  <process ref="robotCommandValidateProcessor"/>
  <process ref="robotCommandEnvelopeProcessor"/>
  <setBody><simple>{"status":"accepted","topic":"${exchangeProperty.robot.mqtt.command.topic}"}</simple></setBody>
  <doCatch>
    <exception>java.lang.Exception</exception>
    <setHeader name="CamelHttpResponseCode"><constant>422</constant></setHeader>
    <setBody><simple>{"error":"ROBOT_POLICY_REJECTED","message":"${exception.message}"}</simple></setBody>
  </doCatch>
</doTry>
<process ref="jsonResponseProcessor"/>
```

该 mock 只验证路由、配置、策略和消息封装，不证明 broker 已收到命令，也不证明机器人已执行。

## 交付边界

- CLI 只调用管理 API，不直连 MQTT broker。
- `outboxStatus=pending` 不代表机器人已收到或已执行。
- `robot state` 可查询管理面状态快照，但 `sourceType=command_status|ack|result|management_snapshot` 都不等同于真实设备在线验收。
- 完整大报文应进入实例日志；审计只保存短摘要和 trace。
- H2 只用于 mock/local POC；真实 dispatcher 使用生产数据库。
- `commands:dispatch-next` 是手动运维入口，不代表自动调度循环已经启用。
- 手动审计清理 API 只作为运维入口保留；默认使用自动 SQL 归档清理。
