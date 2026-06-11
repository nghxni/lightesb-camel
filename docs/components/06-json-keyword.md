# JsonKeyword 外发版

## 用途

JsonKeyword 用于从 JSON 报文中采集指定字段值，配合 H2 缓存和 MySQL 分表同步后，可按 `serviceName`、`serviceVersion`、`keyName`、`jsonValue` 查询实例 ID。

## 典型链路

1. 在业务路由中写入请求/响应缓存。
2. 调用 `jsonKeywordCaptureProcessor` 采集关键字段。
3. 同步服务定时把 H2 中的关键字数据同步到 MySQL 分表。
4. 查询接口按关键字段返回实例 ID 列表。

## 业务路由接入

```xml
<process ref="h2LogCacheProcessor"/>
<process ref="jsonKeywordCaptureProcessor"/>
```

建议先缓存，再采集。采集失败默认不阻断主业务链路。

## 查询入参

| 参数 | 说明 |
| --- | --- |
| `serviceName` | 服务名 |
| `serviceVersion` | 服务版本 |
| `keyName` | JSON 字段名 |
| `jsonValue` | 字段值 |
| `startTime` / `endTime` | 可选时间范围 |
| `maxLimit` | 可选最大返回数量 |

## 示例请求

```bash
curl -G "http://localhost:18083/api/json-keyword/instance-uuids" \
  --data-urlencode "serviceName=DemoOrderSrv" \
  --data-urlencode "serviceVersion=v1.0.0" \
  --data-urlencode "keyName=orderId" \
  --data-urlencode "jsonValue=ORD-001"
```

## 常见问题

- 查询为空：确认业务路由已执行采集，且 `keyName` 与报文字段名完全一致。
- 同步失败：检查 MySQL 连接、建表权限和分表名是否合法。
- 采集不中断业务：这是默认保护行为，需看日志确认采集告警。
