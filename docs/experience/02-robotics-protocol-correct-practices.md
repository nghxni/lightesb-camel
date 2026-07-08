# 机器人协议接入正确做法

## 结论

机器人协议接入先走 mock-first、最小闭环和离线检查，再进入真实联调。验证 route 只用于证明契约，不作为正式产品入口。现场执行闭环完成前，`submit` 只能代表管理 API accepted/outbox queued，不能解释为机器人已执行。

交付资料只引用正式文档、样例、配置键和验收步骤，不引用临时工作目录或一次性执行记录。临时验证结论需要沉淀为本文件、预检文档或交付包中的稳定说明后，才能作为后续实施依据。

## 核心规则

| 规则 | 正确做法 |
| --- | --- |
| 默认样例 | 默认不连接真实 broker、rosbridge、OPC UA Server、Modbus Server、PLC 或 Kafka |
| 协议目标 | topic、service、action、node、register、unitId、host、port 只能由配置和白名单生成 |
| 命令判断 | 不以“已发送”判断成功，必须看 accepted/rejected/result 或明确 outbox queued 状态 |
| 幂等 | `commandId` 是幂等键，重复同 payload 返回稳定结果，不重复执行 |
| 安全 | 默认只开放白名单高层动作，禁止裸写、任意脚本和未登记目标 |
| 凭据 | broker、证书、密码和 endpoint 通过环境变量或安全配置注入，不写入交付包 |
| doctor | `robot doctor --offline` 只做静态检查，不证明真实端点连通 |

## 命令模型

- `RobotCommand` 应区分必填业务字段、可选元数据、服务端补齐字段和版本字段。
- `validate_only` / `dryRun` 只做 schema、能力和策略预检，不下发协议请求。
- `timeoutMs` 表示等待结果超时，`ttlMs` / `expiresAt` 表示提交有效期。
- 默认同一机器人同一时刻只允许一个执行中高层动作；`stop`、`cancel` 可抢占但仍需校验。
- `outboxStatus=pending` 和 `protocolReceipt.dispatched=false` 时，只能解释为 accepted/outbox queued，不代表真实机器人执行。

## 协议经验

### MQTT

- command topic 由 `siteId`、`robotId`、`commandId` 和模板生成。
- ack 只表示接收，result 才能驱动 succeeded/failed。
- 发布前先做 `commandId` 幂等。
- QoS、retain、cleanStart、sessionExpiry 只证明投递策略，不替代业务幂等和安全校验。
- 真实联调前必须明确 TLS/mTLS、ACL、离线会话、重连、重复投递和延迟 result。
- 没有真实固件环境时，应先做模拟固件前置验证：正式 dispatcher 发布 command，模拟客户端订阅 command 并回传 ack/result/telemetry，由 MQTT 观察证据确认 topic、payload、`commandId` 和 `correlationId` 可对齐。
- 模拟固件验证通过不等于真实固件执行通过；如果尚未实现正式 ack/result ingest，只能把 ack/result 作为 MQTT 观察证据，不能声称命令状态已由机器人结果推进。已有 ingest 入口时，可以用显式 local simulator 模式验证 `accepted -> dispatched -> acknowledged -> succeeded`，但仍不能替代现场固件、ACL、弱网和跨实例验收。
- 已有 ingest 入口时，状态机必须允许 result 早于 ack 到达；`timeout` 或 `failed` 后迟到的 `succeeded` 不能覆盖终态；重复 ack/result 第一版不写重复审计。

### rosbridge / ROS2

- 首期优先 rosbridge WebSocket JSON 或 ros2-mqtt-bridge，不建议 LightESB 直接加入 DDS domain。
- ROS topic/service/action 必须来自配置或现场 schema。
- 业务 `robotId` 原样保留；ROS name 中不合法字符通过配置映射。
- rosbridge 只适合低频状态、事件和调试流；高频 TF、图像、点云和 DDS QoS 链路不走默认直连。
- service/action 返回业务拒绝或 result timeout 时，必须输出 `protocol=rosbridge` 的统一错误。

`lightesb-robot-ros2` 当前不交付；ROS2 评估门禁关闭只代表当前不新增组件，不代表 ROS2 原生组件已经产品化。交付包首期继续使用 `RobotRosBridgeSrv`、rosbridge WebSocket JSON 或 ros2-mqtt-bridge，不让 LightESB 直接创建 ROS2 node 或接管 ROS2 graph。

DDS 原生接入当前不作为默认交付能力。只有桥接方案被实际业务要求排除时，才进入二期评估：

`lightesb-robot-dds` 当前不交付；DDS 评估门禁关闭只代表当前不新增组件，不代表 DDS 原生能力已经产品化。

| 准入项 | 交付前必须明确 |
| --- | --- |
| 业务必要性 | 为什么 rosbridge、ros2-mqtt-bridge、MQTT、HTTP、gRPC 或厂商 SDK Gateway 不能满足 |
| ROS2/DDS 契约 | ROS2 发行版、RMW、中间件、domain id、topic、message/action schema、频率和数据量 |
| QoS | reliability、durability、history、deadline、lifespan 等设置及其业务含义 |
| 授权和部署 | DDS Java SDK 授权、native 库、容器镜像、系统依赖、网络发现和端口范围 |
| 安全隔离 | domain 隔离、DDS Security、证书、ACL、网络边界和最小权限 |
| 验证资产 | mock/仿真 domain、QoS 样例、安全样例、异常、offline、重连、热更新和资源释放测试 |

DDS 原生组件即使进入二期，也只允许输出 `RobotTelemetry`、`RobotEvent`、`RobotCommandResult` 或 `RobotTaskState` 管理面摘要。不得承载高频 TF、图像、点云、周期性 setpoint、硬件急停、安全回路、关节伺服或力控闭环。SDK jar 可编译、demo topic 可订阅或单机 happy path 可跑通，都不能解释为产品能力。

### OPC UA

- 节点应分为遥测节点、告警节点和可写命令节点。
- 写节点必须白名单，且写后需要读回、状态节点或业务 result 确认。
- `Security=None` 只适合本机模拟器或早期验证，不代表现场安全配置。
- 真实联调前必须准备 endpoint、安全策略、证书、账号、nodeId、类型、权限和测试窗口。

### Modbus / PLC4X

- register、unitId、functionCode、host、port 都必须来自白名单 alias。
- 写控 alias 必须配置允许值、范围和确认方式。
- `UINT/INT/DINT/REAL`、word-swap、byte-order、exception code 需要模拟器或真实 PLC 验证。
- PLC4X 可作为复杂 PLC 能力候选，但现场点表和验证不足时不应进入默认 runtime。

### 串口、CAN 和实时工业网络

- 串口、RS485、CAN、CANopen、EtherCAT、Profinet 和 EtherNet/IP 首期走边缘 Agent、PLC、运动控制器或厂商 SDK Gateway。
- LightESB 只接收 MQTT、HTTP、gRPC、OPC UA 或 Modbus TCP 等管理面协议。
- 当前不交付串口直连 processor 或 `RobotSerialGatewaySrv` 模板；没有真实设备权限、帧协议、CRC、热插拔、独占访问、断线重连和测试窗口时，不能把字符串解析或 socket 路由说成串口能力。
- 当前不交付 TCP/UDP 通用 payload decoder 或 `RobotFrameDecodeProcessor`；`camel-netty-starter` 可构建只代表候选组件，不代表自研帧协议、UDP 广播或边缘网关接入能力。
- 不通过 LightESB 下发裸 CAN 帧、驱动器 setpoint、周期性关节 setpoint、伺服参数或安全回路控制。
- 当前不交付 SocketCAN 自定义组件；没有真实 CAN 设备、SocketCAN interface、DBC/对象字典、故障码、bus-off/节点离线/重连和权限验证时，不能把 vcan 或裸帧收发说成产品能力。
- CANopen emergency code、厂商故障码和节点离线应映射为 `RobotEvent` 或 `RobotTelemetry.health`。
- EtherCAT、Profinet 和 EtherNet/IP 的实时控制留在 PLC、运动控制器或实时边缘控制器内，LightESB 只处理状态、告警、任务结果和审计 trace。
- 当前不交付 EtherCAT、Profinet 或 EtherNet/IP 网关 SDK 组件；没有真实控制器、SDK 授权、I/O 映射、互锁、故障码、离线/重连和安全测试窗口时，不能把 SDK demo 或模拟 tag 读写说成产品能力。

### 插件化协议适配器

- 自定义适配器只在桥接方案无法满足业务时进入实施，不因协议重要就直接加入默认 runtime。
- 适配器必须默认 disabled，真实 endpoint、账号、证书路径和密码只能通过环境变量或安全配置 key 注入。
- 请求体不能覆盖底层 endpoint、bus id、node、register、frame id、topic、service 或 method。
- 输出必须映射到标准机器人消息，并保留 `protocol`、原始错误、`retryable`、`failureStage`、`routeId` 和 `exchangeId`。
- 必须具备 mock server、模拟器或厂商测试环境，覆盖 offline、权限拒绝、异常码、重连、热更新和动态目标拒绝。
- 必须补齐 doctor 静态检查、部署文档、回滚说明和外发验收步骤。

### Kafka 和外部数据平台

- 默认样例不配置 bootstrap servers，不包含真实 `kafka:` endpoint。
- 先用 mock sink 固化 topic、key、header、schema 和 trace，再接真实 broker。
- 遥测和事件的 `Kafka.KEY` 默认用 `robotId`，保证同机器人消息局部有序。
- `robot.telemetry`、`robot.event`、`robot.command.audit`、`robot.task.state` 是首批建议 topic。
- 真实 Kafka 前必须明确分区数、副本数、retention、压缩、acks、重试、生产者幂等、SASL/TLS、ACL、schema 兼容和死信策略。

### UI 和 AI 生成

- 机器人 UI 只调用稳定管理 API，不直接调用验证 route、mock route 或协议 endpoint。
- 页面必须区分 validate-only、accepted、outbox queued、`protocolReceipt.dispatched=false`、duplicate、rejected、timeout、failed 和 succeeded。
- 命令下发必须有二次确认、危险动作提示、幂等结果展示和审计入口。
- AI route generate 只返回候选 XML 或配置，不自动保存、部署或启用真实 endpoint。
- AI tools 默认只允许只读诊断、配置检查、候选生成和管理 API 查询；写操作必须显式确认并由服务端白名单校验。
- 没有真实 dispatcher、资产库、权限模型和现场端点验收前，AI 不得自动发起机器人动作或修改运行中服务。

AI route generate 当前不交付机器人协议生成模板。已有准入标准只说明未来如何生成候选 XML/配置，不代表 AI 可以自动保存、部署、启用真实 endpoint 或生成现场可执行 route；未提供可复现输入、拒绝样例、安全回归、人工 review 和外发限制说明前，不应产品化。

AI tools 当前不交付机器人接入诊断工具。已有准入标准只说明未来 tools 如何受控读取诊断或管理 API，不代表 AI 可以访问真实资产库、最近心跳、错误日志、dispatcher 或现场端点；未提供工具白名单、权限模型、审计、真实数据源边界和安全回归前，不应产品化。

机器人 UI 页面当前不交付。已有准入标准只说明未来如何实现页面，不代表列表、详情、状态、命令或审计页面已经产品化；未明确真实资产库、在线状态、最近遥测、真实 dispatcher、权限模型和浏览器验收前，不应把 mock/outbox queued 状态做成现场管理台。

## CLI 和 doctor

推荐顺序：

```text
robot doctor --offline
-> robot command validate --file
-> robot list/get/capabilities/state/audit/status
-> robot command submit reliable outbox
-> dispatcher + ack/result 状态闭环
-> 强模拟器/现场执行验收
```

- CLI 只调用稳定管理 API 或本地只读检查，不直接调用验证 route。
- CLI 不接收动态协议目标参数。
- `robot policy list/add/disable` 只调用管理 API denylist，不直接读写数据库、不连接真实机器人、不触发协议调用。
- `robot command validate --file` 不创建命令、不下发协议、不写执行审计。
- `robot command submit --file --yes` 必须明确 outbox queued 不等于真实执行成功。
- `robot command status` 只查已有命令，不提交新命令。
- 真实协议 submit/执行闭环必须等统一 dispatcher、ack/result 状态推进、审计补偿、跨实例幂等、权限/人工确认和真实或强模拟设备验证齐备后再打开。
- 在线 `robot doctor` 必须等真实资产库、最近心跳/遥测数据源、结构化错误日志或日志检索 API、只读权限和站点隔离齐备后再打开；`robot doctor --offline` 不能写成在线诊断。

## 真实联调前置清单

进入真实 broker、rosbridge、OPC UA、Modbus、PLC 或 Kafka 联调前，至少准备：

- endpoint、协议版本、网络连通范围和是否经过代理。
- TLS/mTLS、token、用户名密码、证书和 ACL 要求。
- topic、service、action、node、register、tag 或外部 API schema。
- 允许写控的测试窗口、互锁条件、回滚方式和风险说明。
- offline、timeout、业务拒绝、重启、route reload、重复命令和延迟 result 的验收标准。

## 验收分层

机器人协议验收分三层表达，不能互相替代：

| 层级 | 可证明内容 | 不能证明内容 |
| --- | --- | --- |
| mock baseline | 消息模型、白名单、幂等、审计、错误映射和样例加载 | 真实端点连通和现场设备执行 |
| local simulator | 本机 broker、rosbridge、OPC UA、Modbus、PLC4X 或 Kafka 最小链路 | 客户现场网络、证书、权限、弱网和设备差异 |
| field/product | 真实机器人、PLC、broker、外部系统和现场故障注入 | 不应省略环境、凭据、测试窗口和风险签署 |

交付说明中应使用“mock/local baseline 已完成，field/product 验收后置”这类表述，避免把模拟器结果写成现场验收。

## Review 清单

- 默认样例是否仍是 mock-first。
- 是否写入真实 endpoint、凭据、证书路径或本机路径。
- 请求体是否可能覆盖协议目标。
- 写操作是否有白名单、策略和审计。
- `commandId` 是否在协议下发前做幂等。
- 错误响应是否保留 `protocol`、`commandId`、`robotId`、`correlationId`、`routeId`、`exchangeId`。
- 是否把 mock、模拟器或 outbox queued 误写成真实现场验收。
- CLI 是否直接调用验证 route。
- `robot doctor --offline` 是否被误描述为在线连通性检查。
- 是否引用了临时工作目录、一次性脚本输出或内部路径作为交付证据。
- 是否把“当前综合样例已覆盖，暂不拆分”误写成已经实现了专用模板或真实端点能力。

## 可复用规则句

1. 验证 route 只用于证明契约，不作为正式入口。
2. 默认样例必须 mock-first，真实连接必须显式启用。
3. 未完成现场执行闭环前，submit 只代表 accepted/outbox queued。
4. 请求体不能覆盖协议目标字段。
5. 命令必须幂等，重复 commandId 不能重复执行。
6. ack 不等于成功，result 才能证明最终结果。
7. 默认只开放白名单高层动作。
8. 真实联调前先明确认证、ACL、会话、重连、点表和故障注入方式。
9. robot doctor --offline 只能做离线检查。
10. 本地模拟器验证不等于现场设备验收。
11. 临时工作目录不是交付证据，结论必须沉淀到正式文档。
12. 综合样例已覆盖时，可以决策暂不拆分；不能虚构专用模板或真实互操作能力。
13. gRPC proto 草案和 deadline/retry/metadata/TLS 静态配置键只代表 IDL 与配置契约，不代表已生成 stub、完成真实 gRPC 联调、完成 metadata 注入、完成证书校验或执行重试语义；真实运行语义必须等 endpoint、证书链、鉴权策略、错误注入和重复命令验证用例齐备后再打开。
14. 插件化协议适配器规范只代表准入门禁，不代表 ROS2/DDS、SocketCAN、EtherCAT/Profinet SDK 或厂商私有协议组件已经交付。
15. UI/AI 进入验收标准只代表准入门禁，不代表机器人页面、AI 自动生成、AI tools 写操作或真实动作执行能力已经交付。
16. MQTT 本地 EMQX TLS 单向信任、QoS1、非 retained、非持久会话在线最小投递和发布前 `commandId` 幂等，不代表 mTLS、离线补投、弱网重连、ack/result 状态推进或跨实例一致性已经验证。
17. 管理 API 的 list/get/capabilities/state/audit/status 只代表 mock/management snapshot、本地查询契约或命令状态派生快照；真实资产库、服务包关联、真实在线状态和最近遥测必须等资产模型、状态存储、权限和查询 API 齐备后再打开。
18. submit accepted、HTTP 200、`outboxStatus=pending`、MQTT publish 成功或 `protocolReceipt.dispatched=false` 都不能解释为真实现场执行完成；真实执行闭环必须用状态机、ack/result 持久化、跨实例一致性、审计补偿、权限和强模拟器/现场设备验收共同证明。
19. 正式 dispatcher 验证必须走管理 API、命令账本、审计、outbox、dispatcher、MQTT 接收、状态查询和诊断快照闭环；验证 route 或 demo 路由不能替代正式 dispatcher 证据。
20. 禁用策略应通过管理 API/CLI 和 denylist 管理；不要写进路由 XML，不要让 CLI 直连数据库，也不要把它描述成现场安全互锁。
