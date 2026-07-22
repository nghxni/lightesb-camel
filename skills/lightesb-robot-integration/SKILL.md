---
name: lightesb-robot-integration
description: 机器人、工业协议、边缘 AI 推理门禁和命令 dispatcher 交付指导。处理 MQTT telemetry/command、机器人推理 mock、rosbridge、OPC UA、Modbus、gRPC IDL/mock、机器人命令 validate/status/submit/ingest-receipt、outbox dispatcher、审计归档和现场验收边界时使用。
---

# LightESB 机器人集成

先读：

- `docs/experience/01-robotics-protocol-precheck.md`
- `docs/experience/02-robotics-protocol-correct-practices.md`
- `docs/robot-command-dispatcher-api.md`
- `docs/robot-edge-inference-mock.md`
- `docs/runtime-diagnostics-api.md`
- `proto/robot/robot_command.proto`
- `example/routes/RobotMqttTelemetrySrv/v1.0.0/`
- `example/routes/RobotMqttCommandSrv/v1.0.0/`
- `example/routes/RobotRosBridgeSrv/v1.0.0/`
- `example/routes/RobotOpcUaStationSrv/v1.0.0/`
- `example/routes/RobotModbusGatewaySrv/v1.0.0/`
- `example/routes/RobotGrpcGatewaySrv/v1.0.0/`
- `example/routes/RobotEdgeInferenceSrv/v1.0.0/`

规则：

- 交付包只描述可运行样例、配置、API/CLI 用法和验收边界，不写源码实现路径。
- LightESB 不替代机器人实时控制器、PLC 安全回路、ROS2 DDS 高频链路或硬件急停系统。
- 机器人样例默认可保持 `server.running=false`，用于复制、阅读和 mock 验证。
- 真实设备联调前必须准备 endpoint、凭据、ACL/TLS、点表、测试窗口和回滚方案。
- 不把 mock-first 验证当作真实机器人、broker、rosbridge、OPC UA、Modbus 或 gRPC 互通证明。
- `robot command submit` 进入命令账本、审计和 MQTT outbox；`robot command ingest-receipt` 只把已捕获 MQTT ack/result 回执转交服务端 ingest API；`outboxStatus=pending` 不代表机器人已收到或已执行。
- `ROBOT_POLICY_DENYLIST` 支持 site、robot、protocolProfile 禁用策略；命中启用策略时 `commands:validate` 和 `commands` 返回 `ROBOT_POLICY_REJECTED`，不触发协议调用，拒绝详情包含策略 ID 和禁用来源。
- `commands:validate` 和 `commands` 执行同一高层命令安全策略：`move_to` 检查区域/速度，已配置的 `pick/place` 检查工位/互锁/载荷；策略通过不代表现场安全回路或设备执行已验证。
- 边缘推理样例只允许固定可信 ingress、白名单高层候选、时效/置信度/replay/capability/shared safety 验证；可信审批落地前始终 `submittable=false`，不得调用 submit 或写 outbox。实例内 replay 不代表跨实例保证。
- 本机 EMQX 或强模拟器可用时，使用 `tools/robot-mqtt-firmware-precheck/test_robot_mqtt_firmware_precheck.sh --dispatcher-ingest` 验证 `accepted -> dispatched -> acknowledged -> succeeded`；该结果仍属于 local simulator，不等同于现场机器人验收。
- 无 MySQL 小数据量 POC 可使用 `lightesb.poc.h2-fallback.enabled=true`，机器人命令账本、审计和 outbox 使用 H2；用 `diagnostics snapshot --component robot-command --output json` 确认 `pocH2FallbackEnabled` 和 `robotManagementStorage`。
- 运行态 doctor 用 `lightesb robot doctor --runtime --output json` 或 `diagnostics snapshot --component robot-command --output json` 查看表、outbox、状态快照、补偿、denylist 和最近错误码分布；该检查不连接真实 endpoint。
- H2 fallback 不代表生产级归档、保留、备份恢复或切回 MySQL 后的数据迁移能力。
- 请求体禁止覆盖底层协议目标字段，例如 `topic`、`broker`、`endpoint`、`node`、`register`、`service`、`unitId`。
- 需要离线验证协议路由时，用 HTTP 或 `direct:` 构造 mock payload；策略拒绝、动态协议目标字段等可预期错误应局部返回 400/422，未预期异常再交给全局兜底。
- AVEVA/OPC UA 写控制离线验证时，不连接 `milo-client:`；HTTP mock 只返回固定 `industrial.opcua.write.node` 摘要，请求体包含 `node` 或 `topic` 必须返回 422。

验收：

- 样例配置不包含真实密钥、证书路径、内网地址或生产账号。
- 命令状态语义区分 `accepted`、`dispatched`、`acknowledged`、`succeeded`、`failed`。
- 文档、CLI 和样例的服务名、版本、路径一致。
