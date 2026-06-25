# RobotMqttTelemetrySrv

## 验证目标

使用 mock 方式验证机器人 MQTT 遥测进入 LightESB 后可标准化为统一 JSON，并转发到 HTTP/状态快照下游占位端点。默认不连接真实 MQTT broker。

## Topic 规范

```text
robot/{siteId}/{robotId}/telemetry
robot/{siteId}/{robotId}/heartbeat
```

## Broker 契约

当前样例没有 MQTT 软件也可以验证，默认配置保持：

```properties
robot.mqtt.broker.enabled=false
robot.mqtt.broker.uri=
robot.mqtt.clientId=lightesb-robot-telemetry-{siteId}
robot.mqtt.qos=1
robot.mqtt.retained=false
robot.mqtt.cleanStart=true
robot.mqtt.sessionExpiryInterval=0
robot.mqtt.username.key=ROBOT_MQTT_USERNAME
robot.mqtt.password.key=ROBOT_MQTT_PASSWORD
robot.mqtt.tls.enabled=false
robot.mqtt.mtls.enabled=false
robot.mqtt.tls.truststore.path.key=ROBOT_MQTT_TLS_TRUSTSTORE_PATH
robot.mqtt.tls.truststore.password.key=ROBOT_MQTT_TLS_TRUSTSTORE_PASSWORD
robot.mqtt.tls.keystore.path.key=ROBOT_MQTT_TLS_KEYSTORE_PATH
robot.mqtt.tls.keystore.password.key=ROBOT_MQTT_TLS_KEYSTORE_PASSWORD
robot.mqtt.allowDynamicTopic=false
```

`broker.uri` 为空表示不连接真实 broker；账号、密码、truststore 和 keystore 只声明环境变量 key，不在样例中保存真实凭据、证书路径或密码。`retained=false` 避免命令或状态样例残留，`cleanStart=true` 和 `sessionExpiryInterval=0` 作为 mock-first 默认会话策略。后续有 broker 信息后，再用单独联调配置启用真实 endpoint。

## 本地入口

```text
direct:robot-mqtt-telemetry-mock
```

## 输入示例

```json
{
  "robotId": "quad-001",
  "robotType": "quadruped",
  "siteId": "site-a",
  "timestamp": "2026-06-21T10:00:00+08:00",
  "pose": {"frame": "map", "x": 1.2, "y": 3.4, "yaw": 1.57},
  "battery": {"percent": 82, "charging": false},
  "health": {"status": "OK"}
}
```

## 输出要点

- `messageType=telemetry`
- `robotId`、`robotType`、`siteId`、`sourceProtocol`
- `pose`、`battery`、`health`
- `trace.serviceName`、`trace.serviceVersion`、`trace.routeId`、`trace.exchangeId`

## 验证命令

无 MQTT 软件时，先验证服务包契约和 mock 路由：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotMqttExampleRouteLoadTest,RobotExampleServicePackageTest,RobotMqttPrecheckRouteTest" test
```

该命令不连接真实 broker，只验证 topic pattern、clientId、QoS、retain、cleanStart、sessionExpiryInterval、TLS/mTLS credential key、telemetry 标准化、样例 XML 加载、mock sink 和默认不连接外部端点。
