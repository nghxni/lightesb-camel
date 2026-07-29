---
name: lightesb-logging-observability
description: 配置 servicelog、异常处理、H2 缓存、JsonKeyword 和 StreamCache 时使用。
---

# LightESB 日志与观测

先读：

- `docs/components/02-service-log.md`
- `docs/components/06-json-keyword.md`
- `docs/components/07-stream-cache.md`
- `docs/components/09-exception-handling.md`
- `docs/components/10-h2-jsonkeyword-chain.md`
- `docs/components/14-timer-routes.md`

规则：

- 路由入口、出口、异常分支都应有 `servicelog:`。
- 大报文日志控制 `showBody` 和 `maxBodyLength`。
- H2 缓存先写 `h2LogCacheProcessor`，再按需写 `jsonKeywordCaptureProcessor`。
- H2/StreamCache mock 要显式准备上下文：Request 至少有 `SenderID`，Response 至少有 `ReceiverID`、`<ReceiverID>.ReceiverID`、`<ReceiverID>.ResultCode` 和 `invokeProviderStartTime`。
- H2 fallback 验证 JsonKeyword 前，先用 `/api/lightesb/json-keyword` 注册 keyName，再发业务请求；反查优先用 `/api/lightesb/json-keyword/instance-uuids`。
- 用户要求“无 MySQL 也能演示日志/关键字查询”时，优先使用 `lightesb.poc.h2-fallback.enabled=true`；用 `diagnostics snapshot --component instance-log --output json` 检查 `pocH2FallbackEnabled`、`instanceLogStorage`、`instanceLogQueryStorage`、`jsonKeywordQueryStorage`。
- H2 fallback 只适合小数据量 POC，切回 MySQL 不自动迁移 H2 数据。
- 异常分支返回前调用 `jsonResponseProcessor`。
- 临时验证全局兜底时可用无消费者 `direct:` endpoint，但必须写 `?block=false`，避免 mock 请求因等待消费者而超时。
- Timer 路由没有 HTTP 响应时，主要通过 `servicelog:` 或 Camel 标准日志验收。
- 修改服务日志配置后，用 `POST /api/logging/reload/{fileKey}` 或
  `POST /api/logging/reload/{serviceName}@{serviceVersion}` 重新读取服务目录；
  服务或 fileKey 不存在会返回 `SERVICE_LOG_CONFIG_NOT_FOUND`。

验收：

- 服务日志能定位入口、出口和异常。
- JsonKeyword 查询能按演示字段返回结果或给出可解释空结果。
- StreamCache 样例能在 `lightesb-camel-app/lightesb-StreamCache` 下生成 `.data` 和 `.meta` 文件。
