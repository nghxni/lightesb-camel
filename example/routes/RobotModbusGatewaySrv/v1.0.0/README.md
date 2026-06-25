# RobotModbusGatewaySrv

## 验证目标

使用 mock 方式验证 Modbus TCP 寄存器白名单读写、寄存器映射配置和告警事件映射。默认不连接真实 Modbus Server 或 PLC。

## mock 契约

```properties
robot.modbus.tcp.enabled=false
robot.modbus.tcp.host=
robot.modbus.tcp.port=
```

无 Modbus TCP Server、PLC 或模拟器环境时，保持上述默认值，只通过 `direct:` 和 `mock:` endpoint 验证路由契约。

## 寄存器边界

请求体不接收真实 `register` 或 `modbusRegister` 字段。读写目标必须由配置别名解析：

```properties
robot.modbus.register.heartbeat.read=holding-register:1
robot.modbus.register.commandCode.write=holding-register:10
robot.modbus.register.alarmCode.read=holding-register:20
```

真实 Modbus TCP processor 推荐使用 RegisterMap 配置，便于声明数据类型、单位、缩放和读写权限；旧白名单配置仍兼容：

```properties
robot.modbus.map.heartbeat.register=holding-register:1
robot.modbus.map.heartbeat.access=read
robot.modbus.map.heartbeat.dataType=uint16

robot.modbus.map.commandCode.register=holding-register:10
robot.modbus.map.commandCode.access=write
robot.modbus.map.commandCode.dataType=uint16
```

支持的数据类型：`bit`、`int16`、`uint16`、`int32`、`float32`、`scaled-decimal`。复杂类型、字节序和批量 tag 仍需真实 PLC 联调后再评估 PLC4X。

## 本地入口

```text
direct:robot-modbus-read-mock
direct:robot-modbus-write-mock
direct:robot-modbus-alarm-mock
```

## 聚焦验证

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotOpcUaModbusExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```
