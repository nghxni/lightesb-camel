# 运行时诊断 API 与 CLI

## 用途

运行时诊断用于远程排查 LightESB 当前运行态。它是只读管理 API，不会重载路由、清理数据、关闭连接或修改日志级别。

推荐 Codex 和自动化使用 CLI：

```bash
lightesb diagnostics snapshot --server http://localhost:8080 --output json
lightesb diagnostics warnings --server http://localhost:8080 --output json
lightesb diagnostics snapshot --server http://localhost:8080 --component route-runtime --output json
lightesb robot doctor --server http://localhost:8080 --runtime --output json
```

## API

```text
GET /api/diagnostics/runtime-snapshot
```

查询参数：

| 参数 | 说明 |
| --- | --- |
| `serviceName` | 按服务名过滤。 |
| `serviceVersion` | 按服务版本过滤。 |
| `component` | 按组件过滤。 |

首期组件：

| 组件 | 说明 |
| --- | --- |
| `route-runtime` | 路由文件、routeId、CamelContext 状态、动态 watcher 状态。 |
| `service-log` | 服务日志 logger/config/path 摘要和一致性。 |
| `ai-route-cache` | AI 路由缓存条目数、TTL、命中和清理统计。 |
| `ai-model-session` | AI 路由模型本地 session 数量、TTL 和上限。 |
| `external-datasource` | 外部 DataSource cache 数量、beanName、DataSource 类型和签名 hash。 |
| `robot-command` | 机器人命令账本、审计、outbox、dispatcher、状态快照、补偿、denylist、最近错误码分布、只读 doctor 和审计归档摘要。 |
| `instance-log` | 实例日志 writer 存储模式、H2 fallback 状态、实例日志查询存储、JsonKeyword 查询存储、队列、批次、拒绝任务、最近 flush 和最近错误。 |

当服务端以 `lightesb.route.enabled=false` 启动时，`route-runtime` 组件不注册；按该组件过滤会返回空组件列表。机器人命令 dispatcher 排查应使用 `robot-command` 组件。

## 响应

响应使用管理 API 标准 envelope：

```json
{
  "success": true,
  "data": {
    "runtime": {
      "generatedAt": "2026-06-30T08:00:00Z",
      "uptimeMs": 1000,
      "javaVersion": "21"
    },
    "filters": {
      "serviceName": "DemoSrv",
      "serviceVersion": "v1.0.0",
      "component": "route-runtime"
    },
    "components": [
      {
        "component": "route-runtime",
        "status": "WARN",
        "summary": {
          "totalFiles": 0,
          "totalRoutes": 0,
          "dynamicLoaderActive": false
        },
        "warnings": [
          "dynamic route watcher is not active"
        ]
      }
    ],
    "warnings": [
      {
        "component": "route-runtime",
        "message": "dynamic route watcher is not active"
      }
    ]
  },
  "error": null,
  "timestamp": 1781193600000,
  "requestId": "..."
}
```

## 安全边界

- 该 API 属于正式远程管理 API，应放入部署环境的鉴权、网关审计和访问日志策略。
- CLI 会按 profile 传递 `Authorization: Bearer <token>`。
- 诊断结果只包含摘要，不输出密码、token、完整 prompt、完整 payload、完整 XML/properties、连接串或业务报文正文。
- `robot-command` 不输出完整命令 payload、MQTT topic、target、trace 或 ack/result 报文。`summary.doctor` 输出 `overallStatus`、`connectivityChecked=false` 和 `PASS/WARN/FAIL` 检查项；它只检查管理面运行态，不连接真实 endpoint，不下发命令。
- `instance-log` 不输出请求/响应正文，只输出 writer 运行摘要。无 MySQL POC 时，可检查 `pocH2FallbackEnabled`、`instanceLogStorage`、`instanceLogQueryStorage`、`jsonKeywordQueryStorage` 是否为预期值。
- `warnings` 由服务端生成；CLI 只展示，不在本地推理。

## 错误

| 错误 | 说明 |
| --- | --- |
| `401/403` | 鉴权或权限拒绝。 |
| `5xx` | 服务端诊断组件执行失败。 |
| CLI `69` | HTTP 或服务端 `{success:false}`。 |
| CLI `78` | 未配置 `--server` 或 profile。 |
