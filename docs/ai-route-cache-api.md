# 内置路由推理缓存退出说明

内置路由生成、微调、上下文选择、baseline、最近生成结果和模型 session 已退出，不再提供独立缓存管理。

| 旧 HTTP 接口 | 方法 | 当前行为 |
| --- | --- | --- |
| `/service-management/v1/ai/route/cache/status` | GET | 404，接口不再注册 |
| `/service-management/v1/ai/route/cache` | DELETE | 404，接口不再注册 |
| `/service-management/v1/ai/route/cache/{serviceName}/{serviceVersion}` | DELETE | 404，接口不再注册 |
| `/service-management/v1/ai/route/generate/latest` | GET | 404，接口不再注册 |

旧 `ai route cache status/clear` 和 `ai route latest` 子命令返回参数错误（退出码 64），不发送请求。没有新的缓存参数、响应字段或清理接口替代它们。不要把 404 当作空缓存继续轮询，也不要重新发起旧生成请求。

外部 Agent 在自己的工作目录保存候选和生成上下文；LightESB 通过 `ai route read/prepare/validate/apply` 管理可见服务文件。诊断使用 `route detail/status`、`diagnostics snapshot --component route-runtime` 和 `log snapshot`；`ai-route-cache`、`ai-model-session` 不再属于诊断组件。普通日志、配置缓存及 Action 审批会话保持各自原有契约，不做数据库历史数据删除。

迁移流程见[CLI 命令参考](cli/01-cli-command-reference.md)。
