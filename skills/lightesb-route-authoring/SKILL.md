---
name: lightesb-route-authoring
description: 交付包内编写 HTTP 接口、Camel XML 路由、服务目录和 Undertow 入站端点时使用。
---

# LightESB 路由编写

先读：

- `docs/components/01-http-route-basics.md`
- `docs/components/02-service-log.md`
- `docs/components/03-charset-processing.md`
- `docs/components/14-timer-routes.md`
- `example/README.md`

规则：

- 优先在 `example/` 修改纯演示样例。
- 不在 `lightesb-camel-app/` 新增索引或说明文件。
- HTTP 入站用 `<from uri="undertow:http://0.0.0.0:{{server.port}}/..."/>`。
- 入口放 `requestCharsetProcessor`，出口放 `jsonResponseProcessor`。
- 关键节点使用 `servicelog:`。
- 内部 HTTP 调用优先用 `127.0.0.1:{{server.port}}`、`bridgeEndpoint=true` 和明确超时。
- 无 HTTP 入口的定时任务使用 `timer:`，配置 `HTTP.Listener=false`，验收看日志。

验收：

- `common.config.properties` 有 `HTTP.Listener=true`、`server.port` 和 `system.components=undertowhttp`。
- XML 里没有硬编码生产端口或真实环境地址。
- curl 能返回预期 JSON。
- Timer 路由启动后能按周期输出日志，`routeId` 不冲突。
