# StreamCache 流缓存

## 用途

`lightesb-streamcache` 用于把请求或响应报文异步写入缓存目录，适合大报文留痕、排障和审计。

## 启用

`common.config.properties`:

```properties
system.components=undertowhttp,streamcache
```

## URI

```xml
<to uri="lightesb-streamcache://cache?operateName=Request"/>
<to uri="lightesb-streamcache://cache?operateName=Response"/>
```

Request 缓存依赖 `exchangeProperty.SenderID` 生成文件名；Response 缓存依赖 `exchangeProperty.ReceiverID`，并建议同时提供 `<ReceiverID>.ReceiverID`、`<ReceiverID>.ResultCode` 和 `invokeProviderStartTime` 等响应上下文。离线 mock 如果没有这些属性，可能只创建空目录或在日志中出现缓存写入失败。

常用参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `operateName` | `Request` | 操作名，常用 `Request`/`Response` |
| `asyncEnabled` | `true` | 异步写入 |
| `threadPoolSize` | `10` | 线程池大小 |
| `compressionEnabled` | `true` | 压缩开关 |
| `encryptionEnabled` | `false` | 加密开关 |
| `cachePath` | `./cache` | 端点参数；当前交付包落盘验证优先查看全局 `lightesb.cache.base-directory`，默认 `lightesb-camel-app/lightesb-StreamCache` |

## 验证

- 调用路由后检查 `lightesb-camel-app/lightesb-StreamCache/lightesb/{Request|Response}/{exchangeId}/` 是否生成 `.data` 和 `.meta` 文件。
- 如果只看到空目录，检查日志中的 `AsyncCacheWriter` 错误，通常是 `SenderID`、`ReceiverID` 或响应结果上下文缺失。
- 设置不可写目录，确认日志中能看到写入失败。

## 建议

- 大报文优先开启异步。
- 缓存目录不要放到正式服务配置目录内。
- 演示样例先放 `example/`，需要运行时再复制到正式服务目录。
