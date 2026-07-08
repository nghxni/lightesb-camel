---
name: lightesb-robot-integration
description: 机器人、工业协议和命令 dispatcher 交付指导。处理 MQTT telemetry/command、rosbridge、OPC UA、Modbus、gRPC IDL/mock、机器人命令 validate/status/submit/ingest-receipt、outbox dispatcher、审计归档和现场验收边界时使用。
---

# LightESB 机器人集成

先读：

- `docs/experience/01-robotics-protocol-precheck.md`
- `docs/experience/02-robotics-protocol-correct-practices.md`
- `docs/robot-command-dispatcher-api.md`
- `docs/runtime-diagnostics-api.md`
- `proto/robot/robot_command.proto`
- `example/routes/RobotMqttTelemetrySrv/v1.0.0/`
- `example/routes/RobotMqttCommandSrv/v1.0.0/`
- `example/routes/RobotRosBridgeSrv/v1.0.0/`
- `example/routes/RobotOpcUaStationSrv/v1.0.0/`
- `example/routes/RobotModbusGatewaySrv/v1.0.0/`
- `example/routes/RobotGrpcGatewaySrv/v1.0.0/`

规则：

- 交付包只描述可运行样例、配置、API/CLI 用法和验收边界，不写源码实现路径。
- LightESB 不替代机器人实时控制器、PLC 安全回路、ROS2 DDS 高频链路或硬件急停系统。
- 机器人样例默认可保持 `server.running=false`，用于复制、阅读和 mock 验证。
- 真实设备联调前必须准备 endpoint、凭据、ACL/TLS、点表、测试窗口和回滚方案。
- 不把 mock-first 验证当作真实机器人、broker、rosbridge、OPC UA、Modbus 或 gRPC 互通证明。
- `robot command submit` 进入命令账本、审计和 MQTT outbox；`robot command ingest-receipt` 只把已捕获 MQTT ack/result 回执转交服务端 ingest API；`outboxStatus=pending` 不代表机器人已收到或已执行。
- `ROBOT_POLICY_DENYLIST` 支持 site、robot、protocolProfile 禁用策略；命中启用策略时 `commands:validate` 和 `commands` 返回 `ROBOT_POLICY_REJECTED`，不触发协议调用。
- 本机 EMQX 或强模拟器可用时，使用 `tools/robot-mqtt-firmware-precheck/test_robot_mqtt_firmware_precheck.sh --dispatcher-ingest` 验证 `accepted -> dispatched -> acknowledged -> succeeded`；该结果仍属于 local simulator，不等同于现场机器人验收。
- 无 MySQL 小数据量 POC 可使用 `lightesb.poc.h2-fallback.enabled=true`，机器人命令账本、审计和 outbox 使用 H2；用 `diagnostics snapshot --component robot-command --output json` 确认 `pocH2FallbackEnabled` 和 `robotManagementStorage`。
- H2 fallback 不代表生产级归档、保留、备份恢复或切回 MySQL 后的数据迁移能力。
- 请求体禁止覆盖底层协议目标字段，例如 `topic`、`broker`、`endpoint`、`node`、`register`、`service`、`unitId`。
- 需要离线验证协议路由时，用 HTTP 或 `direct:` 构造 mock payload；策略拒绝、动态协议目标字段等可预期错误应局部返回 400/422，未预期异常再交给全局兜底。
- AVEVA/OPC UA 写控制离线验证时，不连接 `milo-client:`；HTTP mock 只返回固定 `industrial.opcua.write.node` 摘要，请求体包含 `node` 或 `topic` 必须返回 422。

验收：

- 样例配置不包含真实密钥、证书路径、内网地址或生产账号。
- 命令状态语义区分 `accepted`、`dispatched`、`acknowledged`、`succeeded`、`failed`。
- 文档、CLI 和样例的服务名、版本、路径一致。
