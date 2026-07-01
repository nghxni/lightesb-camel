# RobotGrpcGatewaySrv

## 验证目标

定义机器人 gRPC 网关模板的 mock 契约，用于后续把 HTTP 高层动作命令映射到 `RobotCommandService`，以及把遥测/事件桥接到统一机器人消息模型。当前模板不引入 gRPC 组件、不连接真实 gRPC Server、不生成 protobuf 代码。

IDL 草案位于 `proto/robot/robot_command.proto`。该文件只用于评审命令、遥测、事件和 trace 契约，不参与当前 Maven 构建和 Java stub 生成。

## mock 契约

```properties
robot.grpc.enabled=false
robot.grpc.endpoint=
robot.grpc.service.command=RobotCommandService
robot.grpc.service.telemetry=RobotTelemetryService
robot.grpc.deadlineMs=30000
robot.grpc.retry.enabled=false
robot.grpc.retry.maxAttempts=1
robot.grpc.retry.initialBackoffMs=200
robot.grpc.retry.maxBackoffMs=2000
robot.grpc.metadata.allowedKeys=x-request-id,x-correlation-id,x-robot-id,x-site-id
robot.grpc.tls.enabled=false
robot.grpc.mtls.enabled=false
robot.grpc.tls.truststore.path.key=ROBOT_GRPC_TLS_TRUSTSTORE_PATH
robot.grpc.tls.truststore.password.key=ROBOT_GRPC_TLS_TRUSTSTORE_PASSWORD
robot.grpc.tls.keystore.path.key=ROBOT_GRPC_TLS_KEYSTORE_PATH
robot.grpc.tls.keystore.password.key=ROBOT_GRPC_TLS_KEYSTORE_PASSWORD
```

保持 `robot.grpc.enabled=false` 时，只通过 `direct:` 和 `mock:` endpoint 验证消息模型、trace、命令状态和动态协议目标拒绝。

## 本地入口

```text
direct:robot-grpc-command-mock
direct:robot-grpc-telemetry-mock
```

## 边界

- 请求体只允许高层 `RobotCommand` 或标准 telemetry/event 字段。
- 不允许请求体覆盖 `endpoint`、`authority`、`method`、`metadata`、`tls` 等底层协议目标字段。
- deadline、retry、metadata 和 TLS 当前只是静态配置契约；真实 stub 生成、连接、证书校验和重试语义后置到正式 gRPC 切片。
- TLS/mTLS 只声明环境变量 key，不保存真实证书路径或密码。

## 示例

- `samples/request.json`：高层动作命令。
- `samples/response.json`：mock gRPC receipt。

## 聚焦验证

```bash
tools/verify-robot-service-templates.sh
```

该命令只检查模板结构和 JSON 样例，不连接真实 gRPC endpoint。
