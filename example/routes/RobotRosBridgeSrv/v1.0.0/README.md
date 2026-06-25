# RobotRosBridgeSrv

## 验证目标

使用 mock 方式验证 rosbridge WebSocket JSON 的 `subscribe`、`publish`、`call_service` 操作，以及 `move_to/pause/resume/stop` 高层动作到 ROS action/service 的映射。默认不连接真实 ROS2 或 rosbridge。

## mock 契约

```properties
robot.rosbridge.enabled=false
robot.rosbridge.websocket.url=
```

无 rosbridge 或 ROS2 环境时，保持上述默认值，只通过 `direct:` 和 `mock:` endpoint 验证路由契约。

## 本地入口

```text
direct:robot-rosbridge-json-mock
direct:robot-rosbridge-command-mock
```

## 操作映射

| LightESB 动作 | rosbridge 操作 |
| --- | --- |
| `move_to` | `call_service` -> `/robot/{robotId}/action/move_to` |
| `pause` | `call_service` -> `/robot/{robotId}/action/pause` |
| `resume` | `call_service` -> `/robot/{robotId}/action/resume` |
| `stop` | `call_service` -> `/robot/{robotId}/action/stop` |

## 输入示例

```json
{"op":"subscribe","topic":"/robot/quad-001/state","type":"nav_msgs/Odometry"}
```

```json
{
  "commandId": "cmd-ros-001",
  "robotId": "quad-001",
  "commandType": "move_to",
  "target": {"frame": "map", "x": 2, "y": 3},
  "constraints": {"maxSpeed": 0.5},
  "correlationId": "wms-task-ros-001"
}
```

## 拒绝分支

`op` 不属于 `subscribe`、`publish`、`call_service` 时，路由写入 `mock:robotRosRejectSink`，不连接真实 rosbridge。

## 聚焦验证

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotRosBridgeExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```
