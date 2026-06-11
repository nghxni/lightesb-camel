# H2 缓存与 JsonKeyword 链路

## 用途

H2 缓存用于保存请求/响应实例数据；JsonKeyword 链路用于从 JSON 报文中提取关键字段，并支持后续按关键字查询实例。

## 常用处理器

| 处理器 | 用途 |
| --- | --- |
| `h2LogCacheProcessor` | 写入请求/响应缓存 |
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
h2.logcache.executor.pool-size=10
h2.logcache.executor.queue-capacity=1024
h2.logcache.alert.queue-warn-threshold=800
h2.logcache.executor.reject-policy=caller_runs
json.keyword.sync.period=60000
json.keyword.sync.limit=500
json.keyword.cleanup.retention.days=30
```

## 常见问题

- 队列积压：调大线程池或降低写入体积。
- 采集为空：检查 JSON 字段名、服务名和版本。
- MySQL 同步失败：检查连接、建表权限和分表名。
