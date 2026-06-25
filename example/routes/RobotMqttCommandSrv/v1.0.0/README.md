# RobotMqttCommandSrv

## 验证目标

使用 mock 方式验证 HTTP/外部系统命令进入 LightESB 后，通过动作白名单、机器人白名单、能力、在线状态、目标区域、工位互锁和载荷策略校验，再封装为 MQTT command，并生成 ack/result/audit。

## Topic 规范

```text
robot/{siteId}/{robotId}/command/{commandId}
robot/{siteId}/{robotId}/command/{commandId}/ack
robot/{siteId}/{robotId}/command/{commandId}/result
```

## Broker 契约

当前样例没有 MQTT 软件也可以验证，默认配置保持：

```properties
robot.mqtt.broker.enabled=false
robot.mqtt.broker.uri=
robot.mqtt.clientId=lightesb-robot-command-{siteId}
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

`command/ack/result` topic 只能由配置模板生成，不能由请求体动态覆盖；账号、密码、truststore 和 keystore 只声明环境变量 key，不在样例中保存真实凭据、证书路径或密码。`retained=false` 避免机器人收到过期命令，`cleanStart=true` 和 `sessionExpiryInterval=0` 作为 mock-first 默认会话策略。后续有 broker 信息后，再用单独联调配置启用真实 endpoint。

## 本地入口

```text
direct:robot-mqtt-command-mock
```

## 输入示例

```json
{
  "commandId": "cmd-001",
  "robotId": "quad-001",
  "commandType": "move_to",
  "timeoutMs": 30000,
  "target": {"frame": "map", "x": 10.5, "y": 2.1},
  "constraints": {"maxSpeed": 0.5},
  "correlationId": "wms-task-10086"
}
```

## 拒绝用例

- `commandType` 不在 `robot.command.allowedActions`。
- `robotId` 不在 `robot.command.allowedRobotIds`。
- 请求体包含 `topic`、`node`、`register`、`service` 等动态协议目标字段。
- `move_to` 超出目标区域或速度策略。
- `pick/place` 未命中工位白名单、互锁或载荷策略。

## 验证命令

无 MQTT 软件时，先验证服务包契约、命令安全边界和 mock 路由：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotMqttExampleRouteLoadTest,RobotExampleServicePackageTest,RobotMqttPrecheckRouteTest" test
```

该命令不连接真实 broker，只验证 topic pattern、clientId、QoS、retain、cleanStart、sessionExpiryInterval、TLS/mTLS credential key、command topic 生成、动态 topic 拒绝、ack/result/audit、重复 `commandId` 幂等、样例 XML 加载和默认不连接外部端点。
