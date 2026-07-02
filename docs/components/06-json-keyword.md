# JsonKeyword 外发版

## 用途

JsonKeyword 用于从 JSON 报文中采集指定字段值，配合 H2 缓存和 MySQL 分表同步后，可按 `serviceName`、`serviceVersion`、`keyName`、`jsonValue` 查询实例 ID。无 MySQL POC 可开启 `lightesb.poc.h2-fallback.enabled=true`，直接从 H2 缓存表查询。

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

管理 API 可直接完成关键字配置和 H2 fallback 实例反查：

```bash
curl -X POST "http://localhost:8080/api/lightesb/json-keyword" \
  -H "Content-Type: application/json" \
  --data '{"serviceName":"DemoOrderSrv","serviceVersion":"v1.0.0","keyName":"orderId"}'

curl -X POST "http://localhost:8080/api/lightesb/json-keyword/instance-uuids" \
  -H "Content-Type: application/json" \
  --data '{"serviceName":"DemoOrderSrv","serviceVersion":"v1.0.0","keyName":"orderId","jsonValue":"ORD-001","maxLimit":20}'
```

如果使用 `JsonKeywordMysqlSyncSrv` 路由服务提供的业务查询入口，则需要确认该服务已加载并监听对应端口：

```bash
curl -G "http://localhost:18083/api/json-keyword/instance-uuids" \
  --data-urlencode "serviceName=DemoOrderSrv" \
  --data-urlencode "serviceVersion=v1.0.0" \
  --data-urlencode "keyName=orderId" \
  --data-urlencode "jsonValue=ORD-001"
```

## CLI 快速处理

随包 CLI 可直接处理关键字配置和实例反查：

```bash
lightesb keyword list --service-name DemoOrderSrv --service-version v1.0.0 --output json
lightesb keyword add --service-name DemoOrderSrv --service-version v1.0.0 --key-name orderId --yes
lightesb keyword delete --id <keywordConfigId> --yes
lightesb keyword query-instances --service-name DemoOrderSrv --service-version v1.0.0 --key-name orderId --json-value ORD-001 --output json
```

`list/query-instances` 是只读操作；`add/delete` 会修改关键字采集配置，必须带 `--yes`。删除配置不清理历史已采集数据。

## 常见问题

- 查询为空：确认业务路由已执行采集，且 `keyName` 与报文字段名完全一致。
- 配置后仍查询为空：先调用 `GET /api/lightesb/json-keyword?serviceName=...&serviceVersion=...` 确认 keyName 已注册，再发起新的业务请求；关键字配置不会回补注册前的历史请求。
- `temp-only-service` 验证时 `/api/json-keyword/instance-uuids` 返回 404：说明未加载 `JsonKeywordMysqlSyncSrv` 路由；优先用管理 API `/api/lightesb/json-keyword/instance-uuids` 验证 H2 fallback 反查。
- 同步失败：检查 MySQL 连接、建表权限和分表名是否合法。
- 无 MySQL POC 查询为空：确认已开启 `lightesb.poc.h2-fallback.enabled=true`，并且业务请求已经触发 `jsonKeywordCaptureProcessor` 写入 H2。
- 采集不中断业务：这是默认保护行为，需看日志确认采集告警。
