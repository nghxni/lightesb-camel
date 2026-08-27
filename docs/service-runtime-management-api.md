# 服务启停 API

LightESB 通过服务管理 API 或 CLI 修改服务版本的 `server.running`，并等待动态路由加载器确认对应 Camel 上下文真实启动或卸载后再返回。

## 接口

| 操作 | Method | Endpoint |
| --- | --- | --- |
| 启动 | `POST` | `/service-management/v1/runtime/start/{id}` |
| 停止 | `POST` | `/service-management/v1/runtime/stop/{id}` |

`id` 是服务管理记录 ID，请求无 body。

```bash
curl -X POST http://localhost:8080/service-management/v1/runtime/start/svc-1
```

成功响应：

```json
{
  "success": true,
  "data": {
    "id": "svc-1",
    "serviceName": "DemoSrv",
    "serviceVersion": "v1.0.0",
    "serviceStatus": "RUNNING",
    "transitionId": "52be2ef9-73a7-4d7d-a4bc-bcb3a5681292",
    "transitionReused": false,
    "idempotent": false,
    "message": "服务已启动"
  },
  "error": null,
  "timestamp": 1783660800000,
  "requestId": "f15b335c-c600-4325-9a23-1733f967252e"
}
```

- 已满足目标状态的重复请求返回 HTTP `200`、`idempotent=true`，不重复写配置。
- 服务尚未生成或部署路由、部署状态为 `UNDEPLOYED` 时，启动请求返回 HTTP `409`、`SERVICE_NOT_DEPLOYED`；应先生成并保存部署路由。
- 同方向并发请求共享一个 `transitionId`，后到请求返回 `transitionReused=true`。
- 相反方向请求返回 HTTP `409`、`RUNTIME_TRANSITION_IN_PROGRESS`。
- 加载失败、停止失败或等待超时返回 HTTP `409`、`RUNTIME_TRANSITION_FAILED`。
- 失败详情包含实际 `serviceStatus`、`internalStatus`、`diagnosticId`、脱敏 `errorSummary` 和 `timedOut`。
- 超时不会回滚 `server.running`；后台转换可能继续完成，应重新查询服务状态或运行时诊断。

默认等待时间为 30 秒，可通过下列全局参数调整为 1 到 120 秒：

```properties
lightesb.route.transition-timeout-seconds=30
```

错误响应示例：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RUNTIME_TRANSITION_FAILED",
    "message": "等待服务运行状态转换超时",
    "details": {
      "targetStatus": "RUNNING",
      "serviceStatus": "STOPPED",
      "internalStatus": "STOPPED",
      "diagnosticId": null,
      "errorSummary": null,
      "timedOut": true
    }
  },
  "timestamp": 1783660800000,
  "requestId": "cb85ef2e-033c-4b75-b92e-707aa583bf9a"
}
```

CLI 对应命令：

```bash
lightesb service start --id <serviceId> --yes
lightesb service stop --id <serviceId> --yes
```

CLI 收到 HTTP `409` 时以非零状态退出并保留服务端错误摘要；自动化脚本应在失败后查询服务或运行时诊断，不要立即反向覆盖配置。

超时或失败后可通过以下接口读取最终状态：

```text
GET /service-management/v1/detail/{id}
GET /api/diagnostics/runtime-snapshot?serviceName=DemoSrv&serviceVersion=v1.0.0&component=route-runtime
```

服务详情用于核对公开运行状态和部署状态；`route-runtime` 用于读取内部状态、Context 状态、失败阶段、`diagnosticId` 和脱敏摘要。短时间内仍处于转换中时应稍后重查，不要立即发送反方向请求。
