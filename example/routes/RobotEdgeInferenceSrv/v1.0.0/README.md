# RobotEdgeInferenceSrv mock 样例

本服务包只用于 `direct:` + `mock:` 的边缘推理策略验证，默认 `server.running=false`，不提供 HTTP、MQTT 或 gRPC 入口。

向 `direct:robot-edge-inference-mock` 投递 `robot-edge-inference.v1` JSON，并从 `mock:robotEdgeInferenceDecisionSink` 读取 decision。安全候选应为 `pending_approval/submittable=false`；低置信、陈旧、身份不一致、重放冲突或共享安全策略失败应为 `rejected`。

固定 ingress profile 不是生产认证，内存 replay 不是跨实例保证，`pending_approval` 也不是有效审批。当前没有推理 CLI/API、可信 approval provider、持久化 validation decision、AI submit 或 outbox 写入。配置与错误码见 `../../../../docs/robot-edge-inference-mock.md`。
