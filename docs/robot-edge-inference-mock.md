# 机器人边缘 AI 推理 mock 门禁

## 验收步骤

1. 使用 `example/routes/RobotEdgeInferenceSrv/v1.0.0/` 的完整服务目录。
2. 保持 `server.running=false`；该样例没有 HTTP、MQTT 或 gRPC 对外入口。
3. 向 `direct:robot-edge-inference-mock` 投递 `robot-edge-inference.v1` JSON，读取 `mock:robotEdgeInferenceDecisionSink`。
4. 安全候选应返回 `status=pending_approval`、`valid=true`、`submittable=false`；低置信、过期、身份不一致、重放冲突或共享安全策略失败应返回 `status=rejected`。
5. 检查 route 只包含 `direct:` 与 `mock:`，没有命令 submit、outbox 或真实协议 endpoint。

## 必要配置

能力必须显式开启，缺失配置会 fail closed：

```properties
system.components=robotics
robot.ai.inference.enabled=true

robot.ai.inference.ingress.modelKey=warehouse-vlm-v1
robot.ai.inference.ingress.sourceProtocol=direct
robot.ai.inference.ingress.sourcePrincipal=mock-edge-box
robot.ai.inference.ingress.routeId=robot-edge-inference-mock
robot.ai.inference.ingress.siteId=site-a
robot.ai.inference.ingress.allowedRobotIds=quad-001

robot.ai.inference.policyVersion=mock-policy-v1
robot.ai.inference.allowedCommands=move_to
robot.ai.inference.maxAgeMs=5000
robot.ai.inference.allowedClockSkewMs=1000
robot.ai.inference.replay.maxEntries=1000
robot.ai.inference.replay.retentionMs=60000

robot.ai.inference.model.warehouse-vlm-v1.name=warehouse-vlm
robot.ai.inference.model.warehouse-vlm-v1.version=2026-07-15
robot.ai.inference.model.warehouse-vlm-v1.allowedTypes=vlm
robot.ai.inference.model.warehouse-vlm-v1.command.move_to.riskLevel=medium
robot.ai.inference.model.warehouse-vlm-v1.command.move_to.rejectBelow=0.60
robot.ai.inference.model.warehouse-vlm-v1.command.move_to.humanConfirmBelow=0.85
robot.ai.inference.model.warehouse-vlm-v1.command.move_to.maxTtlMs=5000
```

完整资源上限、机器人资产/capability 和区域/速度策略见样例配置。`allowedCommands` 必须是 `robot.command.allowedActions` 的子集；replay retention 必须覆盖推理时效与允许时钟偏差。

## 输入与输出边界

输入只能提出白名单高层候选命令。请求不能自报 `sourceSystem`、`modelKey`、`riskLevel`、`policyVersion`、审批结果或动态 `topic/node/register/service/endpoint`。`observedAt` 必须是当前时效窗口内的 RFC 3339 时间。

通过响应包含推理/机器人身份、candidate digest、模型/策略、命令摘要和检查摘要。响应不会回显媒体 URL、detections 或 raw action vector。常见拒绝码包括：

| 场景 | HTTP | code |
| --- | ---: | --- |
| 输入或时间格式错误 | 400 | `ROBOT_AI_INFERENCE_INVALID` / `ROBOT_AI_INFERENCE_TIME_INVALID` |
| payload 或资源超限 | 413 | `ROBOT_AI_INFERENCE_TOO_LARGE` |
| 同 inferenceId 异 digest | 409 | `ROBOT_AI_INFERENCE_DUPLICATE_CONFLICT` |
| 陈旧或 TTL 超限 | 422 | `ROBOT_AI_INFERENCE_STALE` |
| 来源、身份或模型不匹配 | 422 | `ROBOT_AI_PROVENANCE_INVALID` |
| 置信度过低 | 422 | `ROBOT_AI_CONFIDENCE_TOO_LOW` |
| capability、区域或速度拒绝 | 422 | `ROBOT_POLICY_REJECTED` |

## 未交付能力

- 当前没有推理 CLI 命令或可调用 HTTP/MQTT/gRPC API。
- 固定 ingress profile 只用于 mock，不代表真实认证。
- 内存 replay registry 只覆盖当前单实例生命周期，不提供跨实例或重启后防重放。
- 当前没有可信人工审批 provider、持久化 validation decision 或 AI submit。
- `pending_approval` 不代表已创建审批记录；任何候选都不能据此下发机器人。
