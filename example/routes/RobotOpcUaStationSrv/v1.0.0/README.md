# RobotOpcUaStationSrv

## 验证目标

使用 mock 方式验证 OPC UA 工作站的只读遥测、受限写命令和告警事件映射。默认不连接真实 OPC UA Server。

## mock 契约

```properties
industrial.opcua.enabled=false
industrial.opcua.endpoint.uri=
```

无 OPC UA Server 或 PLC 环境时，保持上述默认值，只通过 `direct:` 和 `mock:` endpoint 验证路由契约。

## 节点边界

- 只读节点：`industrial.opcua.read.node`
- 可写节点：`industrial.opcua.write.node`
- 请求体不允许动态覆盖 OPC UA node。

## 本地入口

```text
direct:robot-opcua-station-read-mock
direct:robot-opcua-station-command-mock
direct:robot-opcua-station-alarm-mock
```

## 聚焦验证

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotOpcUaModbusExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```
