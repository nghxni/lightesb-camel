# RobotClusterDataSrv

## 验证目标

使用 mock 方式验证机器人集群数据管道和外部系统任务接入契约。默认不连接真实 Kafka、WMS、MES 或 dashboard。

## mock 契约

```properties
robot.kafka.enabled=false
robot.kafka.bootstrap.servers=
robot.external.task.enabled=false
robot.external.task.endpoint.uri=
robot.dashboard.endpoint.uri=
```

无 Kafka broker、WMS/MES 或 dashboard 环境时，保持上述默认值，只通过 `direct:` 和 `mock:` endpoint 验证路由契约。

## 本地入口

```text
direct:robot-cluster-telemetry-mock
direct:robot-cluster-event-mock
direct:robot-external-task-mock
direct:robot-task-callback-mock
direct:robot-dashboard-data-mock
```

## 约束

- 遥测和事件使用 `robotId` 作为 Kafka key。
- 外部任务必须提供 `correlationId`，用于关联机器人命令和最终结果。
- 事件至少包含 `robotId`、`siteId`、`correlationId`、`exchangeId` 或等价 trace 字段。

## 输入示例

```json
{
  "taskId": "wms-task-001",
  "robotId": "quad-001",
  "siteId": "site-a",
  "taskType": "move_to",
  "correlationId": "wms-task-001"
}
```

## 聚焦验证

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotClusterDataExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```
