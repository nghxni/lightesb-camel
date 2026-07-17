---
name: lightesb-route-authoring
description: 交付包内编写 HTTP 接口、Camel XML 路由、服务目录、Undertow 入站端点，以及按自然语言要求生成输入/输出/回调 JSON 校验路由时使用。
---

# LightESB 路由编写

先读：

- `docs/components/01-http-route-basics.md`
- `docs/components/02-service-log.md`
- `docs/components/03-charset-processing.md`
- `docs/components/14-timer-routes.md`
- `example/README.md`
- JSON 格式校验任务再读 `docs/components/05-json-schema-validation.md` 和 `docs/cli/01-cli-command-reference.md`。

规则：

- 优先在 `example/` 修改纯演示样例。
- 不在 `lightesb-camel-app/` 新增索引或说明文件。
- 新建服务最小集 = 路由 XML + `common.config.properties` + `service.config.properties`；`log4j2.properties` 运行时自动生成，不要手工创建；Schema、samples 等只在路由实际使用时才添加。
- `<simple>` 体内不混用 `{{占位符}}` 与字面 `}}`（报 `Missing {{ from the text`）；占位符先经 `<constant>` 存入 exchangeProperty 再引用。simple 不支持 `? :` 三元表达式，条件取值用 `<choice>` + `<constant>`。
- HTTP 入站用 `<from uri="undertow:http://0.0.0.0:{{server.port}}/..."/>`。
- 入口放 `requestCharsetProcessor`，出口放 `jsonResponseProcessor`。
- 关键节点使用 `servicelog:`。
- 内部 HTTP 调用优先用 `127.0.0.1:{{server.port}}`、`bridgeEndpoint=true` 和明确超时。
- 内部 HTTP 调用后如果继续处理响应正文，按需 `<convertBodyTo type="java.lang.String"/>`；入口和子路由同名 path header 应先存到 Exchange Property 并 `removeHeader`，避免 Header 多值化。
- 无 HTTP 入口的定时任务使用 `timer:`，配置 `HTTP.Listener=false`，验收看日志。
- 自然语言要求输入、输出或回调 JSON 校验时，不自行生成 Schema。按服务关系调用 `message schema generate`，检查 warnings，再把返回路径写入对应位置的完整校验块。
- route XML 是校验唯一开关，不生成额外配置开关。候选交用户审核后才调用 `ai route apply --save-remote --yes`；apply 失败时保留候选并读取恢复诊断。

验收：

- `common.config.properties` 有 `HTTP.Listener=true`、`server.port` 和 `system.components=undertowhttp`。
- XML 里没有硬编码生产端口或真实环境地址。
- curl 能返回预期 JSON。
- Timer 路由启动后能按周期输出日志，`routeId` 不冲突。
- 校验方向、消息 ID、固定 Schema 文件和 route 中的位置一致。
