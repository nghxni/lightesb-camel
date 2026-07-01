# 实例日志缓存与 JsonKeyword 链路

## 用途

实例日志缓存用于保存请求/响应实例数据；JsonKeyword 链路用于从 JSON 报文中提取关键字段，并支持后续按关键字查询实例。

实例日志生产默认直写 MySQL 查询表；`h2LogCacheProcessor` 是兼容已有路由 XML 的 bean 名。需要无 MySQL 的本地演示或离线 POC 时，可开启 H2 fallback。

## 常用处理器

| 处理器 | 用途 |
| --- | --- |
| `h2LogCacheProcessor` | 异步写入请求/响应实例日志，默认 MySQL writer |
| `jsonKeywordCaptureProcessor` | 采集 JSON 关键字 |
| `jsonKeywordMysqlSyncProcessor` | 同步到 MySQL 分表 |
| `jsonKeywordMysqlCleanupProcessor` | 清理历史分表数据 |
| `jsonKeywordInstanceQueryProcessor` | 查询实例 ID |

## 业务路由建议

```xml
<process ref="h2LogCacheProcessor"/>
<process ref="jsonKeywordCaptureProcessor"/>
```

可通过 Header 标识操作名：

```xml
<setHeader name="h2Log.operateName"><constant>Request</constant></setHeader>
<process ref="h2LogCacheProcessor"/>
```

## 常用配置

```properties
instance.log.writer.storage=mysql
lightesb.poc.h2-fallback.enabled=false
h2.logcache.executor.pool-size=10
h2.logcache.executor.queue-capacity=1024
h2.logcache.alert.queue-warn-threshold=800
h2.logcache.executor.reject-policy=caller_runs
json.keyword.sync.period=60000
json.keyword.sync.limit=500
json.keyword.cleanup.retention.days=30
```

无 MySQL POC：

```properties
lightesb.poc.h2-fallback.enabled=true
```

开启后，实例日志写入/查询、JsonKeyword 实例 UUID 查询和机器人管理 POC 数据强制使用 H2；服务级 `instance.log.writer.storage=mysql` 不会覆盖回 MySQL。

## 常见问题

- 队列积压：调大线程池或降低写入体积。
- 多服务排查：无 tag 的 `lightesb.h2logcache.queue.*` 是聚合值，`lightesb.h2logcache.queue.*.by.service` 可按 `service=serviceName@serviceVersion` 查看明细。
- 生产实例日志写入失败：检查 MySQL 连接、表结构和慢 SQL。
- 本地 POC 不接 MySQL：可设置 `lightesb.poc.h2-fallback.enabled=true`，再用 `diagnostics snapshot --component instance-log --output json` 确认 `instanceLogStorage`、`instanceLogQueryStorage`、`jsonKeywordQueryStorage` 为 `h2-fallback`。
- H2 fallback 只用于几百条级别演示；切回 MySQL 后不会自动迁移 H2 数据。
- 采集为空：检查 JSON 字段名、服务名和版本。
- MySQL 同步失败：检查连接、建表权限和分表名。
