# RobotVda5050Srv

## 验证目标

使用 mock 方式验证业务系统提交的 VDA 5050 命令（`vda_order` / `vda_instant_action`）进入 LightESB 后，通过动作白名单、机器人白名单、能力和在线状态校验，按 `commandId` 幂等去重，再由 `robotVdaOrderEnvelopeProcessor` 构造合规 VDA 5050 JSON body（baseline v3.0.0，非 LightESB envelope），并按 VDA topic 规范路由到 mock sink。本包为 mock-only：不连接真实 AMR 或 MQTT broker。

## Topic 规范（VDA 5050）

```text
uagv/{siteId}/{robotId}/order
uagv/{siteId}/{robotId}/instantActions
```

topic 只能由 `robot.vda5050.order.topic.pattern` / `robot.vda5050.instantAction.topic.pattern` 配置模板生成，不能由请求体动态覆盖。

## 命令模型

复用 LightESB 统一命令模型，VDA order 字段承载在 `payload` 内：

| LightESB 命令字段 | VDA 5050 语义 |
| --- | --- |
| `commandId` | 命令幂等键；建议 `commandId = ${orderId}-${orderUpdateId}`，使每次订单更新成为独立命令 |
| `robotId` / `siteId` | topic 中的 `{robotId}` / `{siteId}` |
| `commandType` | `vda_order` 或 `vda_instant_action` |
| `correlationId` | 与 `payload.orderId` 保持一致 |
| `payload.orderId` / `payload.orderUpdateId` | VDA 订单号与版本，P0 只透传 |
| `payload.nodes` / `payload.edges` | VDA 行驶路径（`vda_order` 必填） |
| `payload.instantActions` | VDA 即时动作（`vda_instant_action` 必填） |
| `payload.version` / `payload.manufacturer` / `payload.serialNumber` | 缺省时由 `robot.vda5050.version` / `robot.vda5050.manufacturer` / `robotId` 补齐 |

`headerId`、`timestamp` 缺省时由 processor 自动生成。

## 本地入口

```text
direct:robot-vda5050-order-mock
direct:robot-vda5050-instant-action-mock
```

## 拒绝用例

- `commandType` 不在 `robot.command.allowedActions`。
- `robotId` 不在 `robot.command.allowedRobotIds`，或机器人未配置能力/处于离线状态。
- 请求体包含 `topic`、`node`、`register`、`service` 等动态协议目标字段。
- `vda_order` 缺 `payload.orderId` / `payload.orderUpdateId` / `payload.nodes` / `payload.edges`。
- `vda_instant_action` 缺 `payload.instantActions`。
- 重复 `commandId` 且请求内容相同：幂等返回 `{"status":"duplicate"}`，不再写入 sink；内容不同则拒绝。

## 样例文件

- `samples/request-order.json`：`vda_order` 命令输入示例。
- `samples/request-instant-action.json`：`vda_instant_action` 命令输入示例。
- `samples/expected-order-mqtt-body.json`：mock sink 收到的 VDA order body 示例（`timestamp` 为运行时生成）。

## 验证命令

无 MQTT 软件时，先验证服务包契约、VDA 字段校验和 mock 路由：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotVda5050RouteTest,RobotExampleServicePackageTest" test
```

该命令不连接真实 broker 或 AMR，只验证 VDA topic pattern、VDA 必填字段校验、动态 topic 拒绝、重复 `commandId` 幂等、样例 XML 加载和默认不连接外部端点。真实 paho-mqtt5 发布由后续 real 服务包承载。
