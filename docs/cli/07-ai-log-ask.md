# 日志问答迁移到外部 Agent

内置日志推理已移除。`log ask` 不再注册，调用返回参数错误（退出码 64），不会发送 HTTP 请求；`POST /api/ai/logging/chat` 不再提供服务（404）。`lightesb.ai.logging.*`、`logAgent`、`aiLogToolService` 和 `AiLogControlSrv` 专属路由已退出，不能通过开关重新启用。

## 使用确定性日志证据

由外部 Codex 或其他 Agent 理解问题，按明确服务与版本采集证据：

```bash
lightesb log health --output json
lightesb log services --output json
lightesb log snapshot --service-name DemoSrv --service-version v1.0.0 --lines 100 --output json
lightesb log instance list --service-name DemoSrv --service-version v1.0.0 --output json
lightesb ai diagnose --service-name DemoSrv --service-version v1.0.0 --output json
```

以上命令使用现有 profile/server 与控制面认证，不需要模型密钥。诊断只读健康与可选路由内容，不触发模型调用。日志证据应按服务、版本、时间窗和 requestId/instanceUuid 关联；更多命令与脱敏边界见[日志治理](01-cli-command-reference.md)和[售后诊断](support-diagnostics.md)。

## 迁移旧配置与路由

1. 识别使用 `service.ai.route=true`、`service.ai.type=logging` 或日志 Agent Bean 的旧服务；升级前备份服务目录和配置。
2. 将问答编排迁移到外部 Agent 的 CLI 调用流程，核对实际采集的证据和目标服务。移除旧运行目录中的专属 Agent 路由须获得该环境授权。
3. 删除已无效的 `lightesb.ai.logging.*` 配置。`--ai-token` / profile `aiToken` 暂保留为客户端兼容字段，不会恢复日志问答，也不是模型 API key。

启用的旧 logging 路由会记录明确的加载失败和迁移提示；`server.running=false` 仍表示正常停用。不要把停止旧服务当作迁移完成。

日志级别修改仍使用显式 `log level set --yes`，与只读证据收集分开授权；移除内置问答不会授权外部 Agent 自动调整级别、清理日志或部署服务。
