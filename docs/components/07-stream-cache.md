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

常用参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `operateName` | `Request` | 操作名，常用 `Request`/`Response` |
| `asyncEnabled` | `true` | 异步写入 |
| `threadPoolSize` | `10` | 线程池大小 |
| `compressionEnabled` | `true` | 压缩开关 |
| `encryptionEnabled` | `false` | 加密开关 |
| `cachePath` | `./cache` | 缓存目录 |

## 验证

- 调用路由后检查缓存目录是否生成数据和元数据文件。
- 设置不可写目录，确认日志中能看到写入失败。

## 建议

- 大报文优先开启异步。
- 缓存目录不要放到正式服务配置目录内。
- 演示样例先放 `example/`，需要运行时再复制到正式服务目录。
