# 机器人协议接入前置验证

## 验收结论

机器人协议接入首期建议采用“桥接优先、受控写入、默认 mock 可验证”的路线：

| 协议/能力 | 决策 | 交付边界 |
| --- | --- | --- |
| MQTT 5 | 采用 | 作为机器人遥测、心跳、命令 ack/result 的主通道之一 |
| rosbridge WebSocket | 采用为桥接路线 | 用 JSON 操作覆盖 topic 订阅、发布、service/action 调用 |
| OPC UA 工作站 | 采用为工业现场路线 | 读节点和受限写节点必须由配置声明 |
| Modbus TCP / PLC4X | 延后进入默认模板 | 可通过寄存器别名白名单验证，真实 PLC 联调后再固化 |
| Kafka / gRPC / Netty | 延后 | 当前只作为候选组件和 IDL 契约验证，不默认启用 |
| Serial / RS485 / CAN / EtherCAT | 替代 | 首期通过边缘 Agent、串口网关、PLC 或运动控制器桥接 |

## 边缘总线和实时工业网络边界

串口、RS485、CAN、CANopen、EtherCAT、Profinet 和 EtherNet/IP 首期不建议由 LightESB 服务端直连。交付包默认只描述边缘网关到 LightESB 的管理面契约：

| 类别 | 推荐路线 | LightESB 接收内容 | 禁止事项 |
| --- | --- | --- | --- |
| 串口 / RS485 / UART / TTL | 边缘 Agent、串口网关、PLC 或厂商控制器转 MQTT/HTTP/Modbus TCP/OPC UA | 设备状态、传感器摘要、任务回执 | 默认不占用串口，不提供串口 route 模板 |
| CAN / CANopen | SocketCAN Agent、MCU 网关或厂商 SDK Gateway | 遥测、健康、故障和任务结果摘要 | 不下发裸 CAN 帧、驱动器 setpoint 或安全回路控制 |
| EtherCAT / Profinet / EtherNet/IP | PLC、运动控制器或实时边缘控制器暴露 OPC UA、Modbus TCP、MQTT、gRPC、HTTP 管理接口 | 工位状态、互锁、告警、任务结果、审计 trace | 不进入微秒级闭环，不透传周期性关节 setpoint |

串口直连当前不作为交付包默认能力。需要服务端直连串口时，必须另行提供设备文件权限、容器挂载、波特率/校验位/停止位、帧边界、CRC、重试、热插拔、独占访问、断线重连、误写风险和测试窗口。没有这些现场条件时，不新增串口 processor 或 `RobotSerialGatewaySrv` 模板。

TCP/UDP 自研帧协议当前不作为交付包默认能力。`camel-netty-starter` 只作为候选组件坐标验证，不代表已经交付通用 payload decoder。需要接入自研上位机、UDP 传感器摘要或边缘网关帧协议时，必须先提供 endpoint、帧边界、字段 schema、字节序、CRC/校验、异常帧、TCP 粘包/半包、UDP 丢包/乱序、限流、动态目标拒绝和测试窗口。

SocketCAN 自定义组件当前不作为交付包默认能力。CAN/CANopen 推荐由 SocketCAN Agent、MCU 网关、机器人控制器或厂商 SDK Gateway 转为管理面摘要。需要服务端直连 CAN 总线时，必须先提供真实 CAN 设备、SocketCAN interface、bitrate、node id、DBC/对象字典、故障码、bus-off/节点离线/重连验证、Linux 权限、容器设备映射和安全测试窗口。

EtherCAT、Profinet 和 EtherNet/IP 网关 SDK 当前不作为交付包默认能力。实时工业以太网推荐继续由 PLC、运动控制器、实时边缘控制器或厂商 SDK Gateway 暴露管理接口。需要新增 SDK 组件时，必须先提供真实控制器、SDK 授权、native 依赖、tag/变量表、I/O 映射、互锁、故障码、离线/重连验证、权限和安全测试窗口。

CAN 网关输出建议：

| 输出类别 | 标准消息 | 必要字段 |
| --- | --- | --- |
| 驱动/关节状态 | `RobotTelemetry` | `robotId`、`jointId`、`position`、`velocity`、`temperature`、`timestamp` |
| 故障和告警 | `RobotEvent` | `robotId`、`eventType`、`faultCode`、`severity`、`trace` |
| 任务/动作结果 | `RobotCommandResult` | `commandId`、`robotId`、`status`、`protocolReceipt` |

实时控制器输出建议：

| 输出 | 标准消息 | 必要字段 |
| --- | --- | --- |
| 状态 | `RobotTelemetry` | `robotId`、`siteId`、`stationId`、`health.status`、`timestamp` |
| 告警 | `RobotEvent` | `eventId`、`robotId`、`eventType`、`severity`、`faultCode`、`trace` |
| 任务结果 | `RobotCommandResult` / `RobotTaskState` | `commandId`、`taskId`、`status`、`resultPayload`、`protocolReceipt` |

以上内容只定义交付接入边界，不代表现场 CAN、EtherCAT、Profinet 或 EtherNet/IP 互操作已完成。

## 插件化协议适配器准入

交付包当前只提供协议适配器准入规则，不交付 ROS2/DDS、SocketCAN、EtherCAT/Profinet SDK 等自定义组件。项目确需新增适配器时，必须先证明现有桥接路线无法满足业务。

自定义适配器进入实施前至少需要：

- 明确 endpoint、topic/service/action、点表、帧格式、QoS、时序、认证、证书、ACL、故障码、重连和验收窗口。
- 默认 disabled，真实 endpoint、账号、证书路径和密码只能通过环境变量或安全配置 key 注入。
- 请求体不能覆盖底层 endpoint、bus id、node、register、frame id、topic、service 或 method。
- 输出必须映射到标准 `RobotTelemetry`、`RobotEvent`、`RobotCommandResult` 或 `RobotTaskState`。
- 必须提供 mock server、模拟器或厂商测试环境，覆盖 offline、权限拒绝、异常码、重连、热更新和动态目标拒绝。
- 必须补齐 doctor 静态检查、部署文档、回滚说明和外发验收步骤。

该规范是后续组件评估门禁，不代表任何自定义组件已经产品化。

## UI 和 AI 进入验收

交付包当前只定义机器人 UI、AI route generate 和 AI tools 的进入验收标准，不交付机器人管理页面或机器人 AI 自动执行能力。

机器人 UI 页面当前不作为交付包能力；评估结论只代表当前不新增页面，不代表机器人管理台已经交付。UI 实现前必须先明确真实资产库、真实在线状态、最近遥测、真实 dispatcher、权限模型、审计来源和浏览器验收条件。

UI 进入实施前必须满足：

- 只调用稳定机器人管理 API，不直接调用验证 route、mock route 或协议 endpoint。
- 明确数据来源：mock/management snapshot、reliable outbox、真实资产库或真实 dispatcher。
- 区分 validate-only、accepted、outbox queued、`protocolReceipt.dispatched=false`、duplicate、duplicate_conflict、rejected、timeout、failed 和 succeeded。
- 命令下发必须有二次确认、危险动作提示、幂等结果展示和审计入口。
- 浏览器验收覆盖空态、加载、错误、无权限、离线、超时、重复提交、后端不可达、桌面和移动宽度。

AI route generate / AI tools 进入实施前必须满足：

AI route generate 当前不作为交付包能力；评估结论只代表当前不新增机器人协议生成模板，不代表机器人协议 AI 生成已经产品化。交付前必须先提供可复现输入、候选输出、拒绝样例、安全回归、人工 review 记录和外发限制说明。

AI tools 当前不作为交付包能力；评估结论只代表当前不新增机器人接入诊断工具，不代表机器人 AI 诊断已经产品化。交付前必须先提供工具白名单、权限模型、审计、真实数据源边界、拒绝样例、安全回归和人工 review 记录。

- AI route generate 只返回候选 XML 或候选配置，不自动保存、部署或启用真实 endpoint。
- 协议目标必须来自模板、白名单、能力、点表或服务包配置，不能由 prompt 透传底层 topic/node/register/service/action/endpoint。
- AI tools 默认只允许只读诊断、配置检查、候选生成和管理 API 查询；写操作必须显式确认并由服务端白名单校验。
- AI 输出必须标注 mock/local baseline、validate-only、outbox queued 或 field/product 语义。
- 没有真实 dispatcher、资产库、权限模型和现场端点验收前，AI 不得自动发起机器人动作或修改运行中服务。

## 安全约束

动作命令只允许 `move_to`、`pick`、`place` 作为首期自动执行动作。每条写控制路径必须满足：

- `robot.command.allowedActions` 声明动作白名单。
- `robot.command.allowedRobotIds` 声明机器人白名单。
- `robot.asset.{robotId}.capabilities` 命中动作能力。
- `robot.asset.{robotId}.online=true`。
- `move_to` 必须满足目标区域和速度策略。
- `pick/place` 必须满足工位白名单、工位互锁和载荷策略。
- 请求体不允许动态覆盖 `topic`、`node`、`register`、`service` 等协议目标。
- 写操作必须生成 ack/result/audit，重复 `commandId` 不得重复执行。

## 消息模型

前置验证确认同一机器人模型可以承载五类消息：

| 类型 | 必要字段 |
| --- | --- |
| 状态/遥测 | `messageType=telemetry`、`robotId`、`siteId`、`timestamp`、`trace` |
| 命令 | `messageType=command`、`commandId`、`robotId`、`siteId`、`commandType`、`correlationId` |
| 事件 | `messageType=event`、`eventId`、`robotId`、`siteId`、`eventType`、`trace.correlationId` |
| 任务 | `messageType=task`、`taskId`、`robotId`、`siteId`、`taskType`、`status`、`commandId` |
| 回执 | `commandId`、`robotId`、`status`、`timestamp`、`correlationId` |

## 关键配置

```properties
system.components=robotics
robot.siteId=site-a
robot.command.allowedActions=move_to,pick,place
robot.command.allowedRobotIds=robot-001,arm-001
robot.asset.robot-001.capabilities=move_to
robot.asset.robot-001.online=true
robot.asset.arm-001.capabilities=pick,place
robot.asset.arm-001.online=true

robot.policy.target.minX=0
robot.policy.target.maxX=20
robot.policy.target.minY=0
robot.policy.target.maxY=20
robot.policy.maxSpeed=0.8
robot.policy.allowedStationIds=station-a
robot.station.station-a.interlocked=true
robot.policy.maxPayloadKg=5.0
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
robot.mqtt.command.topicPattern=robot/{siteId}/{robotId}/command/{commandId}
robot.mqtt.command.ackTopicPattern=robot/{siteId}/{robotId}/command/{commandId}/ack
robot.mqtt.command.resultTopicPattern=robot/{siteId}/{robotId}/command/{commandId}/result
```

OPC UA 写节点必须由服务配置指定：

```properties
industrial.opcua.read.node=ns=2;s=Robot.Station.State
industrial.opcua.write.node=ns=2;s=Robot.Station.Command
```

Modbus 建议通过寄存器别名映射，不从请求体接收真实寄存器地址：

```properties
robot.modbus.register.heartbeat.read=holding-register:1
robot.modbus.register.commandCode.write=holding-register:10
```

真实 Modbus TCP processor 推荐使用 RegisterMap 配置声明类型、单位、缩放和读写权限；旧白名单配置仍兼容：

```properties
robot.modbus.map.heartbeat.register=holding-register:1
robot.modbus.map.heartbeat.access=read
robot.modbus.map.heartbeat.dataType=uint16

robot.modbus.map.commandCode.register=holding-register:10
robot.modbus.map.commandCode.access=write
robot.modbus.map.commandCode.dataType=uint16
robot.modbus.map.commandCode.min=0
robot.modbus.map.commandCode.max=65535
```

支持的数据类型：`bit`、`int16`、`uint16`、`int32`、`float32`、`scaled-decimal`。`scaled-decimal` 可配合 `scale`、`offset` 和 `unit` 使用。

## 本地验证

默认验证使用 mock 路由，不连接真实机器人、PLC、MQTT broker 或 rosbridge：

```powershell
mvn -q -pl lightesb-camel-core test
```

控制面聚合验证：

```powershell
mvn -q -pl lightesb-camel -am test
```

只运行机器人协议前置验证：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotMqttExampleRouteLoadTest,RobotRosBridgeExampleRouteLoadTest,RobotOpcUaModbusExampleRouteLoadTest,RobotClusterDataExampleRouteLoadTest,RobotExampleServicePackageTest,RobotMqttPrecheckRouteTest,RobotProtocolPrecheckRouteTest,RouteProcessorRegistrarTest" test
```

只运行 MQTT 阶段 1 mock 收口验证：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotMqttExampleRouteLoadTest,RobotExampleServicePackageTest,RobotMqttPrecheckRouteTest" test
```

只运行 rosbridge 阶段 2 mock 收口验证：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotRosBridgeExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```

只运行 OPC UA + Modbus 阶段 3 mock 收口验证：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotOpcUaModbusExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```

只运行集群数据阶段 4 mock 收口验证：

```powershell
mvn -q -pl lightesb-camel-core "-Dtest=RobotClusterDataExampleRouteLoadTest,RobotExampleServicePackageTest,RobotProtocolPrecheckRouteTest" test
```

候选组件坐标预检使用可选 profile：

```powershell
mvn -q -pl lightesb-camel-core "-Drobot.protocol.precheck=true" "-Dtest=RobotProtocolComponentCoordinatePrecheckTest" test
```

## 阶段 1-4 mock 样例

当前交付包已提供阶段 1 到阶段 4 的 mock-first 样例，默认 `server.running=false`，不连接真实 MQTT broker、rosbridge、OPC UA Server、Modbus TCP Server、Kafka 或机器人。

| 阶段 | 样例目录 | 验证内容 |
| --- | --- | --- |
| 阶段 1 | `example/routes/RobotMqttTelemetrySrv/v1.0.0/`、`example/routes/RobotMqttCommandSrv/v1.0.0/` | MQTT telemetry 标准化、命令封装、ack/result/audit |
| 阶段 2 | `example/routes/RobotRosBridgeSrv/v1.0.0/` | rosbridge JSON `subscribe/publish/call_service` 和动作映射 |
| 阶段 3 | `example/routes/RobotOpcUaStationSrv/v1.0.0/`、`example/routes/RobotModbusGatewaySrv/v1.0.0/` | OPC UA 读写节点分离、Modbus 寄存器别名白名单、工业告警转机器人事件 |
| 阶段 4 | `example/routes/RobotClusterDataSrv/v1.0.0/` | Kafka 风格出流契约、外部任务接入、任务回调、dashboard 数据 |

这些样例用于验证服务包结构、路由契约、配置边界和 mock sink，不代表真实协议端点互操作已经完成。

## MQTT broker 契约 mock

没有 MQTT broker 软件时，先使用 MQTT 样例中的 mock 契约验证，不需要安装新软件：

- `robot.mqtt.broker.enabled=false`，默认不启用真实 broker。
- `robot.mqtt.broker.uri=`，默认不保存 broker 地址。
- `robot.mqtt.clientId`、`robot.mqtt.qos`、`robot.mqtt.retained`、`robot.mqtt.cleanStart`、`robot.mqtt.sessionExpiryInterval` 只定义联调投递契约。
- `robot.mqtt.username.key`、`robot.mqtt.password.key`、TLS truststore/keystore path/password key 只声明环境变量名；真实 MQTT route 使用环境变量把账号密码注入 `paho-mqtt5` endpoint，不交付真实凭据、证书路径或密码。
- telemetry、heartbeat、command、ack、result topic 都由配置模板生成。
- `robot.mqtt.allowDynamicTopic=false`，请求体不能覆盖 topic。

该契约只证明配置键、topic 模板和拒绝边界稳定，不证明真实连接、订阅、发布、QoS、TLS/mTLS、离线会话、重连或 broker ACL。

## 验收状态分层

当前交付包采用 mock/local baseline 与 field/product gate 分层表达验收状态：

| 验收域 | 已完成基线 | 仍需现场或产品化验收 |
| --- | --- | --- |
| 功能链路 | MQTT、rosbridge、OPC UA、Modbus、PLC4X、Kafka 风格出流、外部任务和 dashboard mock 契约 | 真实机器人资产库、服务包关联、真实在线状态、最近遥测、真实协议 dispatcher、真实 Kafka/WMS/MES/dashboard |
| 百台规模 | 100 台 mock robot 心跳、遥测、事件、状态快照、ack/result/audit 和重复 `commandId` 幂等 | 真实 broker/机器人/PLC/外部系统的吞吐、弱网、乱序、离线会话和跨实例一致性 |
| 安全 | 白名单、能力、策略、动态协议目标拒绝、默认样例不连真实端点 | 人工确认、现场 ACL、证书轮换、权限模型和审计留存 |
| 可观测 | 管理 API 响应、协议错误对象、日志、命令表、审计表和 Kafka 风格 mock sink | 真实日志检索、指标、trace、告警和审计补偿 |
| 文档 | 样例 README、配置边界、联调清单和正确做法 | 后续真实 dispatcher、UI、AI tools、自定义组件和现场模板同步 |

交付验收时应明确写出“mock/local baseline 已完成，field/product 验收后置”。默认样例继续保持 mock-first，不应因为 baseline 完成而自动连接真实端点。

## MQTT 端到端 mock 场景

没有 MQTT broker 软件时，可以先验证 LightESB 内部 MQTT 主链路闭环：

- telemetry 输入标准化为统一机器人 JSON，并写入 HTTP/状态 mock sink。
- command 输入生成 `robot/{siteId}/{robotId}/command/{commandId}` topic。
- 成功 command 生成 MQTT command、ack、result、audit。
- 请求体动态 `topic` 被拒绝，只写 rejected audit。
- 重复 `commandId` 不重复下发，只写 duplicate audit。

该场景不证明真实 broker 的连接、订阅、发布、QoS、TLS/mTLS、重连、离线会话或 ACL。

## MQTT 样例服务包加载

MQTT 样例还提供服务包级 XML 加载验证：

- 加载 `RobotMqttTelemetrySrv/v1.0.0/robot-mqtt-telemetry-route.xml`，通过 `direct:robot-mqtt-telemetry-mock` 验证 HTTP/状态 mock sink。
- 加载 `RobotMqttCommandSrv/v1.0.0/robot-mqtt-command-route.xml`，通过 `direct:robot-mqtt-command-mock` 验证 command/ack/result/audit mock sink。
- 验证所需 processor bean、配置占位和 XML route 可启动运行。
- 验证运行时 endpoint 不包含真实 MQTT broker endpoint。

该验证使用测试 stub 替代真实 `servicelog` 日志写入，不证明日志落盘、日志查询或真实 broker 连接。

## MQTT 阶段 1 mock 验证矩阵

当前交付结论：MQTT 阶段 1 mock 验证已收口，可作为真实 broker 联调前的验收基线；本地 EMQX 已完成明文 MQTT `1883` 和 TLS 单向信任 `8883` 下 telemetry、command、ack/result、动态 topic 拒绝、路由热更新连接重建，以及 QoS1、非 retained、非持久会话在线投递的最小验证，但不能据此承诺现场 broker、mTLS、离线会话、重连或 ACL 已验证。

| 验证项 | 可复验证据 | 当前结论 | 未覆盖范围 |
| --- | --- | --- | --- |
| 默认不连接 broker | MQTT 样例配置、`RobotExampleServicePackageTest` | 默认 `broker.enabled=false` 且 `broker.uri` 为空，不会误连真实 broker | 真实 broker 地址、认证、连接失败重试 |
| 凭据契约 | MQTT 样例 README、配置 key、只读检查 | 只声明账号、密码、TLS truststore/keystore path/password key；真实 route 可通过环境变量注入账号密码，不交付真实用户名、密码、证书路径或证书密码 | 现场凭据注入、证书链、密钥轮换 |
| 投递策略 | MQTT 样例配置、`RobotExampleServicePackageTest`、本地 EMQX TLS 验证 | 样例声明 QoS、retain、cleanStart 和 sessionExpiryInterval；2026-06-23 已复验 command 外部订阅收到 QoS1、`retained=false`，并以 `cleanStart=true`、`sessionExpiryInterval=0` 建立非持久会话 | 离线会话、补投、乱序、重复投递和弱网重连 |
| topic 模板 | MQTT 样例配置、`RobotMqttPrecheckRouteTest` | telemetry、heartbeat、command、ack、result topic 由模板生成 | 现场 topic ACL、共享订阅、保留消息 |
| telemetry 标准化 | `RobotMqttPrecheckRouteTest` | mock telemetry 可标准化并写入 HTTP/状态 mock sink | 真实吞吐、乱序、离线补发、异常 payload |
| command 闭环 | `RobotMqttPrecheckRouteTest` | command 可生成 topic，并产出 ack/result/audit | 真实设备 ack/result 时延、丢包、投递确认 |
| 动态 topic 拒绝 | `RobotMqttPrecheckRouteTest` | 请求体动态 `topic` 被拒绝，只写 rejected audit | broker ACL 拒绝和非法发布错误映射 |
| 重复 `commandId` | `RobotMqttPrecheckRouteTest`、机器人管理 API 测试、只读检查 | mock route 重复命令不重复下发；真实 MQTT command route 在发布前使用持久化唯一键识别重复 `commandId`，重复同内容命令不再次发布 | 跨实例分布式锁、ack/result 状态推进幂等 |
| 管理 API outbox 前置 | 只读 `robot doctor`、机器人管理 API 测试 | 静态检查 `ROBOT_COMMAND`、`ROBOT_AUDIT_LOG`、`ROBOT_COMMAND_OUTBOX` 初始化 SQL、审计归档/清理接口文档和 outbox 幂等测试 | 真实 broker 重投递、跨实例分布式锁和 ack/result 状态推进 |
| 服务包 XML 加载 | `RobotMqttExampleRouteLoadTest` | 两个 MQTT 样例 XML route 可启动并跑通 mock sink | 生产部署热加载、真实日志落盘和查询 |

## 真实 MQTT broker 联调前置清单

进入真实 broker 联调前，需要先由现场或项目方提供以下信息。信息未齐备时，继续使用 mock 验证，不建议安装 broker 或改默认样例连接真实端点。

- broker 地址、端口、协议 URI 和测试网络连通方式。
- MQTT 协议版本，优先 MQTT 5；如为 MQTT 3.1.1，需确认降级影响。
- TLS/mTLS 要求、CA、客户端证书和证书校验方式。
- 用户名、密码或证书凭据来源，必须通过环境变量、CI secret 或安全配置注入。
- telemetry、heartbeat、command、ack、result 的 topic 前缀、模板、站点和机器人 ID 规则。
- QoS、retain、clean session/session expiry、离线消息、重复投递和顺序保证策略。
- clientId 命名规则和同名 clientId 冲突处理策略。
- 订阅、发布、通配符、共享订阅和非法 topic 的 ACL 规则。
- 可清理的测试 topic 命名空间、测试账号和 broker 审计日志查询方式。
- 断线重连、broker 重启、ack/result 延迟、重复消息和路由热更新后的连接重建验收标准。

真实 MQTT route 的认证账号密码必须由运行环境提供。更新 route XML 或服务包配置时，LightESB 可通过路由热加载生效；修改 Java 处理器、依赖、Spring 配置或启动参数后需要重启应用。

## 本地 EMQX MQTT 验证

本地 MQTT 5 已完成最小联调：

- Broker：本地 EMQX，明文端口 `1883`，TLS 端口 `8883`。
- 测试工具：MQTTX Desktop。
- telemetry：LightESB 订阅 `robot/site-a/+/telemetry`，MQTTX 发布 `robot/site-a/quad-001/telemetry`，服务日志记录 `messageType=telemetry`、`robotId=quad-001`、`topic=robot/site-a/quad-001/telemetry`。
- command：LightESB HTTP 入口发布到 `robot/site-a/quad-001/command/cmd-real-001`，响应包含 `status=published`，服务日志记录 command envelope。
- ack/result：LightESB 订阅 `robot/site-a/+/command/+/ack` 和 `robot/site-a/+/command/+/result`，服务日志记录 ack accepted 和 result succeeded。
- 动态 topic 拒绝：请求体包含 `topic` 时返回 `BIZ003 权限不足`，错误信息为 `robot command cannot override protocol target field: topic`，未发布到 MQTT。
- 机器人 API 异常响应：按机器人 MQTT command 服务契约和 HTTP command request URI 识别，不依赖固定服务名；动态 topic 拒绝预期返回 `403`，响应包含 `status=rejected`、`protocol=mqtt5`、`errorCode=BIZ003`、`commandId`、`robotId` 和 `correlationId`。ack/result 等 MQTT consumer 异常继续走通用异常响应。
- 热更新重建：reload command 服务路由后，command producer、ack consumer、result consumer 均继续工作。
- TLS：已通过 EMQX `8883`、MQTTX TLS、JVM truststore 和 LightESB `ssl://127.0.0.1:8883` 完成 telemetry、command、ack/result、动态 topic 拒绝和 route reload 后连接重建最小验证；运行态已确认 LightESB/Java 连接 `8883`，不再连接 `1883`。
- MQTT 投递策略：2026-06-23 通过 Java Paho MQTT v5 客户端连接 EMQX TLS `8883`，先订阅 `robot/site-a/quad-001/command/cmd-real-001`，再通过 LightESB HTTP command 入口发布；外部订阅收到 QoS1、`retained=false` 的 command payload，telemetry、ack、result 也被 LightESB consumer 消费并写入服务日志。本轮只验证最小在线投递语义，未验证离线会话补投。

该验证只覆盖本地 broker 的 telemetry consumer、command producer、ack/result consumer、动态 topic 拒绝、明文/TLS 热更新后连接重建、TLS 单向信任、QoS1/非 retained/非持久会话的在线最小投递和成功路径日志落盘。动态 topic 拒绝发生在第一条业务日志前，HTTP route 由 CamelContext 级全局异常处理接管异常。管理 API 已支持本地命令记录、审计记录和 `commandId` 持久化幂等；真实 broker 重投递、mTLS、broker 重启/断网重连、离线会话补投和 broker ACL 仍需现场或后续环境单独验证。交付样例仍保持 mock-first 默认配置，不携带真实账号、密码或证书。

## 机器人管理 API Reliable Outbox

管理 API 已提供命令账本、审计和 MQTT outbox 持久化，用于验证命令查询、审计、重启后幂等和可靠派发队列：

| 接口 | 用途 |
| --- | --- |
| `POST /service-management/v1/robots/{robotId}/commands` | 提交高层动作命令，同事务写入命令账本、审计和 MQTT outbox |
| `GET /service-management/v1/robots/{robotId}/commands/{commandId}` | 查询持久化命令结果 |
| `GET /service-management/v1/robots/{robotId}/audit` | 查询命令审计，支持 `commandId`、`eventType` 过滤 |
| `DELETE /service-management/v1/robots/audit?retentionDays=N&dryRun=true|false` | 手动清理过期审计日志，`retentionDays` 必须大于等于 1；默认清理路径是服务端自动 SQL 归档 |

持久化与 outbox 边界：

- 命令提交后保持 `accepted`，`protocolReceipt.outboxStatus=pending` 表示已进入 MQTT outbox。
- 幂等使用请求签名 SHA-256 hash；只保存脱敏请求摘要，不保存完整请求、token、密码、证书路径、broker endpoint 或动态协议目标字段。
- 审计日志默认每天凌晨 1 点归档到 `${lightesb.deployment.backup-dir}/audit/ROBOT_AUDIT_LOG-yyyyMMddHHmmss.sql`，数据库保留 1 个月，SQL 备份保留 24 个月。
- 管理 API 当前分为只读基线、`commands:validate` 基线和 reliable outbox 提交三类；accepted/outbox pending 不代表真实协议执行成功。
- CLI 已增加 `robot command validate --file` 预检能力，并且只能调用 `commands:validate`，不得创建命令、下发协议或写执行审计。
- CLI 已增加 `robot command submit --file --yes` 提交能力；它只调用 `/commands` 管理入口，必须显式确认，并拒绝 `mode=validate_only` 或 `dryRun=true`。`protocolReceipt.dispatched=false` 时不能解释为真实协议下发或机器人执行。
- 审计记录覆盖 submitted、duplicate、duplicate_conflict 和可识别 rejected。
- 审计清理只删除审计日志，不删除命令记录，避免破坏 `commandId` 幂等。
- 当前清理接口是手动最小能力；大表场景建议后续接入分批删除、定时保留策略和管理权限控制，避免单次大事务或误删。
- 当前已具备 MQTT outbox 首期闭环；真实设备或强模拟器、ack/result 状态推进持久化、跨实例幂等、审计补偿和现场故障注入仍需独立验收。
- 该能力不代表真实 MQTT/rosbridge/OPC UA/Modbus 下发、ack/result 状态推进、跨实例分布式锁或审计补偿已经完成。
- 正式 `robot doctor` 接入运行态数据源已评估为后置能力；交付包当前只保留 `robot doctor --offline` 静态检查，不连接运行中后端、数据库、日志索引或真实端点。真实资产库、最近心跳、错误日志、权限边界和运行态查询 API 稳定后再重新打开。

## gRPC IDL 契约

交付包包含 `proto/robot/robot_command.proto`，用于评审机器人 gRPC 网关契约。当前只定义：

- `RobotCommandService`：命令提交、命令预检和命令结果查询。
- `RobotTelemetryService`：遥测和事件发布。
- 命令、结果、遥测、事件、trace、协议回执和统一错误对象。

交付包中的 `RobotGrpcGatewaySrv` 样例还声明 deadline、retry、metadata allowlist、TLS/mTLS 开关，以及 TLS truststore/keystore path/password 的环境变量 key。这些键只用于配置契约评审和离线检查，不保存真实证书路径、证书密码或连接地址。

该 proto 和配置键不代表已经生成 Java stub，也不代表真实 gRPC Server 已完成互操作。真实 deadline、retry、metadata 注入、TLS/mTLS 证书校验、鉴权、流式接口和厂商 SDK 对接已评估为后置能力，必须等真实或强模拟 gRPC endpoint、证书链、鉴权策略、错误注入和重复命令验证用例齐备后再打开。

## rosbridge 样例服务包加载

rosbridge 样例提供服务包级 XML 加载验证：

- 加载 `RobotRosBridgeSrv/v1.0.0/robot-rosbridge-route.xml`。
- 通过 `direct:robot-rosbridge-json-mock` 验证 `subscribe`、`publish`、`call_service` 和 unsupported op 拒绝分支。
- 通过 `direct:robot-rosbridge-command-mock` 验证高层动作到 rosbridge `call_service` payload，以及 result mock sink。
- 验证所需 processor bean、配置占位和 XML route 可启动运行。
- 验证运行时 endpoint 不包含真实 rosbridge WebSocket endpoint。

该 mock 验证不证明真实 rosbridge、ROS2 topic、service 或 action 已完成互操作；源码仓库内另有 WSL 本机 Docker rosbridge + ROS2 demo 节点最小自动化，用于验证 WebSocket、demo topic/service、offline、重启恢复和 route reload。

## rosbridge 阶段 2 mock 验证矩阵

当前交付结论：rosbridge 阶段 2 mock 验证已收口，可作为真实 rosbridge/ROS2 联调前的验收基线；源码仓库内已完成 WSL 本机 Docker rosbridge + ROS2 demo 最小自动化，但交付包默认样例仍不连接真实 rosbridge，不能据此承诺现场 WebSocket、真实机器人 action 或鉴权已验证。

| 验证项 | 可复验证据 | 当前结论 | 未覆盖范围 |
| --- | --- | --- | --- |
| 默认不连接 rosbridge | rosbridge 样例配置、`RobotExampleServicePackageTest` | 默认 `robot.rosbridge.enabled=false` 且 `robot.rosbridge.websocket.url` 为空，不会误连真实 rosbridge | 真实 rosbridge URL、鉴权、连接失败重试 |
| JSON 操作分流 | `RobotRosBridgeExampleRouteLoadTest`、`RobotProtocolPrecheckRouteTest` | `subscribe`、`publish`、`call_service` 可进入对应 mock sink | 真实 WebSocket 帧、ROS message type、订阅生命周期 |
| unsupported op 拒绝 | `RobotRosBridgeExampleRouteLoadTest` | 非白名单 `op` 被拒绝，只写 rejected mock sink | rosbridge 错误码、非法请求连接处理 |
| 高层动作映射 | `RobotRosBridgeExampleRouteLoadTest`、`RobotProtocolPrecheckRouteTest` | `move_to` 可映射为 `/robot/{robotId}/action/{commandType}` call_service payload | 真实 action/service 名称、参数 schema、result schema |
| 安全校验 | `RobotProtocolPrecheckRouteTest` | 动作白名单、机器人白名单、能力、在线状态和策略校验可复用 | 真实机器人离线、ROS action timeout、取消和失败细分状态 |
| 服务包 XML 加载 | `RobotRosBridgeExampleRouteLoadTest` | `RobotRosBridgeSrv` XML route 可启动并跑通 mock sink | 生产部署热加载、真实日志落盘和查询 |

## rosbridge 本机真实自动化补充

源码仓库验证记录：

- 使用本地镜像 `lightesb/rosbridge-jazzy:local` 启动 ROS2 Jazzy + `rosbridge_server` + `demo_nodes_py`。
- 直连 rosbridge 验证 `/chatter` topic 订阅、`/add_two_ints` service 调用和 missing service 错误。
- 通过 `RobotRosBridgeSrv` HTTP route 验证真实 `call_service` 成功、missing service 映射为 `protocol=rosbridge` / `errorCode=NET002`、rosbridge offline、重启恢复和 route reload。
- 源码仓库已新增 `move_to` action/service 语义仿真自动化：使用 ROS2 service 字符串载荷承载编码后的业务 JSON，覆盖成功 result、业务拒绝、timeout、cancel、offline、重启恢复和 route reload；该验证仍不等同真实 ROS2 action server 或现场机器人运动控制。
- rosbridge service 返回 `result=false`、`values.success=false` 或 `values.successful=false` 时，对外机器人 HTTP API 应返回 `status=rejected`、`protocol=rosbridge`，不得误报成功；result 等待超时映射为 `NET001`，连接失败或业务拒绝映射为 `NET002`。
- 2026-06-24 已完成 WSL 本机复验，自动化脚本和 rosbridge 相关聚焦回归均通过，测试后无残留容器或端口监听。
- 2026-06-25 已完成 `move_to` 仿真自动化复验，覆盖成功 result、越界拒绝、timeout、cancel、offline、rosbridge 重启恢复和 route reload 后恢复；同日 rosbridge 相关聚焦回归 20 个测试通过。

限制：本机自动化使用 ROS2 demo service 和仿真 service，不代表真实机器人 action feedback、现场鉴权、现场网络、真实路径规划或安全互锁已验证。

## ROS Bridge 接入规范和映射

交付包首期只建议使用 rosbridge WebSocket JSON 或 ros2-mqtt-bridge 接入 ROS/ROS2，不建议让 LightESB 直接加入 DDS domain。默认样例继续以 `RobotRosBridgeSrv` 作为综合基线；如项目需要独立遥测和命令模板，可在现场 topic/action schema 明确后再拆分。

`lightesb-robot-ros2` 自定义组件当前不作为交付包能力。评估结论只代表当前不新增组件，不代表 ROS2 原生组件已经实现；交付包仍以 `RobotRosBridgeSrv`、rosbridge WebSocket JSON 和 ros2-mqtt-bridge 作为 ROS2 接入路线。

首期约束：

| 项目 | 约束 |
| --- | --- |
| topic/service/action | 只能从配置、能力映射表或现场 schema 生成，请求体不得动态覆盖 |
| `robotId` 和 ROS name | 业务 `robotId` 原样保留；ROS name 中不合法字符通过配置映射，例如 `quad-001` -> `quad_001` |
| 遥测 | 只接低频状态、事件和调试流；高频 TF、图像、点云和 DDS QoS 链路不走默认 LightESB 直连 |
| 命令 | service response 可表达 accepted/rejected；需要 feedback、cancel 或长时间执行的动作应使用 action 或等价仿真契约 |
| 安全 | 高层动作仍必须经过白名单、能力、在线状态、策略和审计校验 |
| 错误 | WebSocket 断开、service/action 不存在、schema mismatch、timeout 和业务拒绝统一输出 `protocol=rosbridge` 错误对象 |

## DDS 原生接入评估

交付包当前不交付 DDS 原生组件，也不建议让 LightESB 直接加入 ROS2/DDS domain。只有 rosbridge、ros2-mqtt-bridge、MQTT、HTTP、gRPC 或厂商 SDK Gateway 无法满足业务时，才进入 DDS 二期评估。

`lightesb-robot-dds` 自定义组件当前不作为交付包能力。评估结论只代表当前不新增组件，不代表 DDS 原生接入已经实现。

DDS 原生接入实施前至少需要：

- 明确 ROS2 发行版、RMW、中间件、domain id、topic、message/action schema、QoS、频率和数据量。
- 明确 DDS Java 客户端授权、native 库、容器镜像、系统依赖、网络发现和端口范围。
- 明确 domain 隔离、DDS Security、证书、ACL、网络边界和最小权限。
- 提供 mock/仿真 domain，覆盖连接、订阅、发布、异常、offline、重连、热更新和资源释放。
- 输出只映射到 `RobotTelemetry`、`RobotEvent`、`RobotCommandResult` 或 `RobotTaskState` 摘要。

限制：

- 不用 DDS 原生组件承载高频 TF、图像、点云、周期性控制 setpoint、硬件急停或安全回路。
- SDK jar 能编译、demo topic 可订阅或单机 happy path 可跑通，都不代表产品能力。
- 未完成强模拟器或真实现场验收前，不进入默认 runtime、默认模板、UI、CLI 或 AI 生成。

ROS topic 映射建议：

| topic 类别 | 示例 | 标准消息 | 说明 |
| --- | --- | --- | --- |
| 状态/位姿 | `/robot/{rosRobotName}/state`、低频 `/tf` 摘要 | `RobotTelemetry` | 保留 `robotId`、`pose`、`frame`、`timestamp` |
| 电量/健康 | `/battery_state`、`/diagnostics` | `RobotTelemetry` / `RobotEvent` | 异常状态转事件 |
| 命令回执 | `/robot/{rosRobotName}/command/{commandId}/result` | `RobotCommandResult` | 保留 `commandId` 关联 |
| 任务事件 | `/robot/{rosRobotName}/task_event` | `RobotEvent` / `RobotTaskState` | 可对接 Kafka 或外部任务系统 |
| 调试 topic | `/chatter` | 测试日志或事件 | 只用于联调 |

ROS action/service 映射建议：

| `commandType` | ROS 映射 | 说明 |
| --- | --- | --- |
| `move_to` | `/robot/{rosRobotName}/action/move_to` action 或白名单 service | accepted 后等待 result；timeout 映射 `NET001` |
| `pause` / `resume` | pause/resume service 或 action | 不绕过任务状态机 |
| `stop` | stop service/action | 上层停止命令，不替代硬件急停 |
| `cancel` | cancel service/action | 取消未完成命令或可取消动作 |
| `pick` / `place` | 现场机械臂 service/action 或 PLC/OPC UA 桥接 | 未确认现场 schema 前不进默认模板 |

## 真实 rosbridge/ROS2 联调前置清单

进入真实 rosbridge 或 ROS2 联调前，需要先由现场或项目方提供以下信息。信息未齐备时，继续使用 mock 验证，不建议安装 rosbridge 或改默认样例连接真实端点。

- rosbridge WebSocket URL、协议、端口、网络连通方式和是否经过反向代理。
- rosbridge Server 版本、ROS/ROS2 发行版、机器人或仿真环境版本。
- TLS、鉴权、token、用户名密码或网络隔离要求，真实凭据不能写入交付文件。
- 状态 topic、message type、频率、关键字段和异常 payload 样例。
- 需要发布或调用的 topic/service/action 名称、参数 schema、超时和 result schema。
- `move_to`、`pause`、`resume`、`stop` 的真实 action/service 映射和失败状态枚举。
- unsupported op、非法 topic、非法 service 和参数错误的返回格式。
- 断线重连、订阅恢复、重复命令、延迟 result、action timeout 和取消命令的验收标准。
- 可清理的测试命名空间、测试机器人或仿真场景、日志查看方式和故障注入方式。
- 路由热更新时 WebSocket 连接释放、重建和未完成命令状态迁移的验收标准。

## OPC UA + Modbus 样例服务包加载

OPC UA 和 Modbus 样例提供服务包级 XML 加载验证：

- 加载 `RobotOpcUaStationSrv/v1.0.0/robot-opcua-station-route.xml`。
- 通过 `direct:robot-opcua-station-read-mock`、`direct:robot-opcua-station-command-mock`、`direct:robot-opcua-station-alarm-mock` 验证只读遥测、受限写命令、告警事件和审计 mock sink。
- 加载 `RobotModbusGatewaySrv/v1.0.0/robot-modbus-gateway-route.xml`。
- 通过 `direct:robot-modbus-read-mock`、`direct:robot-modbus-write-mock`、`direct:robot-modbus-alarm-mock` 验证寄存器白名单读写和告警事件 mock sink。
- 验证所需 processor bean、配置占位和 XML route 可启动运行。
- 验证运行时 endpoint 不包含真实 OPC UA Milo、PLC4X 或 Modbus TCP endpoint。

该验证不证明真实 OPC UA Server、Modbus TCP Server、PLC 或模拟器已完成互操作。

## OPC UA + Modbus 阶段 3 mock 验证矩阵

当前交付结论：OPC UA + Modbus 阶段 3 mock 验证已收口，可作为真实工业端点联调前的验收基线；本机 OPC UA 模拟器已完成 `Security=None`、固定写节点、动态 node 拒绝、offline 异常和 route reload 后重建的最小真实端点验证。该结果仍不能承诺现场 OPC UA Server、PLC、寄存器时序或设备安全互锁已验证。

| 验证项 | 可复验证据 | 当前结论 | 未覆盖范围 |
| --- | --- | --- | --- |
| OPC UA 默认不连接 Server | OPC UA 样例配置、`RobotExampleServicePackageTest` | 默认 `industrial.opcua.enabled=false` 且 `industrial.opcua.endpoint.uri` 为空，不会误连真实 Server | 真实 endpoint、认证、安全策略、证书、连接失败重试 |
| OPC UA 节点边界 | OPC UA 样例配置、`RobotProtocolPrecheckRouteTest` | 只读节点和可写节点由配置声明，请求体不能动态覆盖 `node` | 真实 namespace、数据类型、权限、写入状态码 |
| OPC UA 服务包 XML 加载 | `RobotOpcUaModbusExampleRouteLoadTest` | `RobotOpcUaStationSrv` XML route 可启动并跑通 read/command/alarm/audit mock sink | 生产部署热加载、真实日志落盘和查询 |
| OPC UA 模拟器最小真实验证 | 本机模拟器自动化脚本 | 固定写节点、直连读回、动态 node 拒绝、offline 非 200 和文件级 route reload 后重建通过 | 证书/用户名密码、安全加密、现场 Server 权限、复杂数据类型和业务互锁 |
| Modbus 默认不连接 PLC | Modbus 样例配置、`RobotExampleServicePackageTest` | 默认 `robot.modbus.tcp.enabled=false` 且 host/port 为空，不会误连 PLC 或模拟器 | 真实 host、port、unitId、连接失败重试 |
| Modbus RegisterMap 和类型转换 | Modbus 样例配置、`IndustrialProcessorTest`、`RobotProtocolPrecheckRouteTest` | 读写寄存器由配置别名解析，请求体不能动态覆盖 `register` / `modbusRegister` / `unitId`；真实 processor 支持 `bit`、`int16`、`uint16`、`int32`、`float32`、`scaled-decimal`、`scale`、`offset`、`unit`、`min/max` 和读写权限 | 真实寄存器地址偏移、字节序/字序、批量 tag、写入确认和异常码 |
| Modbus 服务包 XML 加载 | `RobotOpcUaModbusExampleRouteLoadTest` | `RobotModbusGatewaySrv` XML route 可启动并跑通 read/write/alarm mock sink | PLC4X 驱动连接、轮询时序、重连和写入确认 |
| PLC4X Modbus 实验服务包 | `RobotPlc4xModbusSrv`、聚焦测试 | PLC4X 已进入默认运行时依赖，但仍只作为并行实验服务包启用；可通过 `plc4xAddress` 白名单验证单 tag、多 tag、复杂类型和写控边界，不默认连接真实 PLC | 真实 PLC 互操作、字节序/word-swap 矩阵、现场异常码和长时间重连 |

## 真实 OPC UA / Modbus 联调前置清单

进入真实 OPC UA Server、Modbus TCP Server、PLC 或模拟器联调前，需要先由现场或项目方提供以下信息。信息未齐备时，继续使用 mock 验证，不建议安装 Server/模拟器或改默认样例连接真实端点。

- OPC UA endpoint URI、Server 版本、namespace、节点清单、读写权限和安全策略。
- OPC UA 鉴权方式、用户名密码或证书来源、证书信任链、证书有效期和安全模式。
- OPC UA 只读遥测节点、可写命令节点、数据类型、写入成功/失败状态码和告警节点映射。
- Modbus TCP host、port、unitId、PLC/模拟器型号、寄存器区、地址偏移规则和网络连通方式。
- Modbus 寄存器别名、读写方向、数据类型、字节序/字序、缩放系数、写入确认和异常码映射；默认 RegisterMap 可声明 `register`、`access`、`dataType`、`scale`、`offset`、`unit`、`min/max`，PLC4X 实验包可声明 `plc4xAddress`。
- `pick/place` 与 PLC/OPC UA 工作站命令的真实字段映射、互锁规则、载荷限制和失败状态枚举。
- 断线重连、Server/PLC 重启、读写超时、重复命令、写入半成功和告警风暴的验收标准。
- 可清理的测试工位、测试设备或模拟器场景、日志查看方式和故障注入方式。
- 路由热更新时 OPC UA session、Modbus TCP connection 释放、重建和未完成命令状态迁移的验收标准。

## 集群数据样例服务包加载

集群数据样例提供服务包级 XML 加载验证：

- 加载 `RobotClusterDataSrv/v1.0.0/robot-cluster-data-route.xml`。
- 通过 `direct:robot-cluster-telemetry-mock` 和 `direct:robot-cluster-event-mock` 验证 Kafka 风格 telemetry/event mock sink，包含 `Kafka.KEY` 和 topic header。
- 通过 `direct:robot-external-task-mock` 和 `direct:robot-task-callback-mock` 验证外部任务接入和任务回调 mock sink。
- 通过 `direct:robot-dashboard-data-mock` 验证 dashboard 数据 mock sink。
- 验证所需 processor bean、配置占位和 XML route 可启动运行。
- 验证运行时 endpoint 不包含真实 Kafka、HTTP 外部 API 或 dashboard endpoint。

该验证不证明真实 Kafka broker、WMS/MES、dashboard 或外部数据平台已完成互操作。

## 集群数据阶段 4 mock 验证矩阵

当前交付结论：集群数据阶段 4 mock 验证已收口，阶段 1-4 mock 服务包闭环已完整；真实 Kafka broker、WMS/MES、dashboard 或外部数据平台联调尚未开始，不能据此承诺现场分区、顺序、重试、消费者语义或外部 API 已验证。

Kafka topic、key 和 header 建议：

| Topic | Key | 消息 | 当前证据 |
| --- | --- | --- | --- |
| `robot.telemetry` | `robotId` | `RobotTelemetry` | mock sink 保留 `Kafka.KEY` 和 topic header |
| `robot.event` | `robotId` | `RobotEvent` | mock sink 保留 `Kafka.KEY` 和 topic header |
| `robot.command.audit` | `robotId` 或 `commandId` | 命令审计摘要 | 真实 Kafka 出流待 broker 联调 |
| `robot.task.state` | `robotId` 或 `taskId` | `RobotTaskState` | 外部任务和 task callback mock sink 已验证契约 |

交付包默认不包含真实 `kafka:` endpoint，也不配置 bootstrap servers。真实 Kafka 联调时再按现场分区、压缩、SASL/TLS、ACL、schema 兼容和死信策略补充配置。

| 验证项 | 可复验证据 | 当前结论 | 未覆盖范围 |
| --- | --- | --- | --- |
| 默认不连接 Kafka | 集群数据样例配置、`RobotExampleServicePackageTest` | 默认 `robot.kafka.enabled=false` 且 `robot.kafka.bootstrap.servers` 为空，不会误连真实 broker | 真实 broker、认证、TLS、ACL、连接失败重试 |
| telemetry/event 出流契约 | `RobotClusterDataExampleRouteLoadTest`、`RobotProtocolPrecheckRouteTest` | telemetry/event 可进入 mock sink，并以 `robotId` 作为 `Kafka.KEY` | 真实分区、顺序、压缩、事务、消费者位点 |
| 外部任务接入 | `RobotClusterDataExampleRouteLoadTest`、`RobotProtocolPrecheckRouteTest` | 外部任务通过 `correlationId` 进入 task ingress mock sink | 真实 WMS/MES API、鉴权、幂等、错误码和补偿 |
| 任务回调 | `RobotClusterDataExampleRouteLoadTest` | task callback 默认走 mock sink，不连接真实外部系统 | 真实回调 endpoint、签名、超时、重试和死信 |
| dashboard 数据 | `RobotClusterDataExampleRouteLoadTest` | dashboard mock route 可输出站点、在线机器人和任务统计 | 真实查询 API、缓存、分页、权限和状态快照存储 |
| 服务包 XML 加载 | `RobotClusterDataExampleRouteLoadTest` | `RobotClusterDataSrv` XML route 可启动并跑通 telemetry/event/task/callback/dashboard mock sink | 生产部署热加载、真实日志落盘和查询 |

## 真实 Kafka / 外部系统联调前置清单

进入真实 Kafka broker、WMS/MES、dashboard 或外部数据平台联调前，需要先由现场或项目方提供以下信息。信息未齐备时，继续使用 mock 验证，不建议安装 Kafka 或改默认样例连接真实端点。

- Kafka bootstrap servers、broker 版本、topic、分区数、副本数、retention、压缩和消息大小限制。
- Kafka 鉴权方式、TLS/SASL、ACL、生产者 idempotence、acks、重试、超时和死信策略。
- `robot.telemetry`、`robot.event`、`robot.command.audit`、`robot.task.state` 等 topic 的 key、header、schema 和兼容策略。
- `Kafka.KEY` 分区策略：遥测和事件默认 `robotId`，任务状态和命令审计需明确使用 `robotId`、`taskId` 还是 `commandId`。
- WMS/MES 任务接入 API、鉴权、幂等键、任务字段、错误码、重试和补偿策略。
- 任务回调 endpoint、签名/验签、超时、重试、重复回调和失败告警策略。
- dashboard 查询的数据源、刷新周期、状态快照存储、权限、分页和历史数据保留策略。
- 弱网、broker 重启、消费者滞后、重复消息、乱序消息、外部 API 超时和回调失败的验收标准。
- 可清理的测试 topic、测试租户/站点、测试任务编号、日志查看方式和故障注入方式。
- 路由热更新时 Kafka producer、外部 HTTP client、未完成任务状态和回调队列的释放、重建和迁移验收标准。

## 后续落地顺序

1. 先使用已提供的阶段 1-4 mock 样例完成服务包结构和配置契约检查。
2. MQTT 阶段 1 mock 验证已收口；本地 EMQX 已完成 telemetry、command、ack/result、动态 topic 拒绝、明文/TLS 热更新重建、TLS 单向信任、QoS1、非 retained 和非持久会话在线投递的最小真实 broker 验证。
3. MQTT mTLS、离线会话、断线重连、ack/result 状态推进和跨实例一致性已评估为后置能力；现场 broker、证书链、离线会话策略、故障注入窗口、状态推进存储和跨实例一致性方案齐备后再单独复验。
4. rosbridge/ROS2 本机 demo 最小自动化已完成；现场 rosbridge/ROS2 前置清单齐备后，再推进真实 action/service 联调，验证状态订阅、动作调用、result 回写、异常 op 拒绝、鉴权和热更新重建。
5. OPC UA 已完成本机 `Security=None` 模拟器最小验证；前置清单齐备后，再推进现场 OPC UA / Modbus 工业端点联调，验证证书/权限、节点读写、寄存器读写、异常映射、热更新连接释放和安全互锁。
6. Kafka / 外部系统前置清单齐备后，再推进真实数据平台联调，验证 topic/key/header、外部任务、任务回调、dashboard 查询和热更新连接释放。
7. rosbridge、OPC UA 和 Modbus 当前保持综合样例或网关样例；只有真实产品化需要独立部署、独立权限或独立生命周期时，才拆分遥测/命令专用模板。
8. 阶段 1-4 mock 服务包闭环已经完整；gRPC 当前只有 mock 模板、`proto/robot/robot_command.proto` IDL 草案和静态配置契约，CLI、UI、AI 生成和自定义 DDS/CAN/EtherCAT 组件继续后置。插件化协议适配器规范、UI/AI 进入验收标准只作为准入门禁，不代表对应功能已交付。
9. 真实机器人资产注册、服务包关联、运行态资产库、真实在线状态和最近遥测已评估为后置能力；当前管理 API 只代表 mock/management snapshot 和本地查询契约，不代表真实资产库或现场运维数据源。
10. 真实协议 dispatcher、ack/result 状态推进、跨实例幂等和现场设备执行闭环已评估为后置能力；当前 submit 只代表 accepted/outbox queued，不代表现场机器人执行成功。
