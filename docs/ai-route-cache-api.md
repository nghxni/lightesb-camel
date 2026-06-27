# AI 路由缓存管理 API

本文档说明交付包中 AI 路由缓存的状态查询与清理接口，用于排查上下文选择或 baseline 复用情况。

BasePath：`/service-management/v1/ai/route/cache`

## 接口总览

| 能力 | Method | Endpoint | 说明 |
| --- | --- | --- | --- |
| 查询缓存状态 | GET | `/status` | 查询上下文选择缓存和 baseline 缓存状态 |
| 清理全部缓存 | DELETE | `` | 清理全部 AI 路由缓存 |
| 按服务清理缓存 | DELETE | `/{serviceName}/{serviceVersion}` | 清理指定服务版本关联缓存 |

## 查询缓存状态

```bash
curl "http://localhost:8080/service-management/v1/ai/route/cache/status"
```

响应 `data` 包含：

- `contextSelection`：上下文选择缓存统计，含 `entryCount`、`ttlSeconds`、`maxSize`、`hits`、`misses`、`expired`、`puts`、`cleared`。
- `baseline`：第二步 baseline 缓存统计，字段同上。
- `serviceIndexSize`：服务维度索引数量。
- `lastCleanupTime`：最近清理时间戳，毫秒。
- `lastCleanupRemoved`：最近清理条目数。

## 清理缓存

清理全部：

```bash
curl -X DELETE "http://localhost:8080/service-management/v1/ai/route/cache"
```

按服务清理：

```bash
curl -X DELETE "http://localhost:8080/service-management/v1/ai/route/cache/DemoAiSrv/v1.0.0"
```

响应 `data.removed` 表示本次移除的缓存条目数，`data.status` 是清理后的状态快照。

## CLI 对应命令

```bash
lightesb ai route cache status
lightesb ai route cache clear --yes
lightesb ai route cache clear --service-name DemoAiSrv --service-version v1.0.0 --yes
```

`cache clear` 是写操作，必须显式传 `--yes`。

## 边界

- API 和日志只输出统计、数量、TTL、清理结果和 cache key hash。
- 不输出完整 prompt、文档、脚本、XML 或 properties 内容。
- 缓存命中不跳过后端校验。
