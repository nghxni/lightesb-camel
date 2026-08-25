---
name: lightesb-route-authoring
description: 交付包内编写 HTTP 接口、Camel XML 路由、服务目录、Undertow 入站端点，以及按自然语言要求生成输入/输出/回调 JSON 校验路由时使用。
---

# LightESB 路由编写

先读 `docs/components/16-route-static-preflight.md`，再按任务选择最小上下文：

| 场景 | 补充文档/样例 |
| --- | --- |
| HTTP、内部 HTTP | `docs/components/01-http-route-basics.md`、`docs/components/02-service-log.md`、`docs/components/03-charset-processing.md`、`example/routes/http-undertow/` |
| Timer | `docs/components/14-timer-routes.md`、`example/routes/timer/v1.0.1/` |
| JSON Schema | `docs/components/05-json-schema-validation.md`；仅在用户授权 CLI/远程操作时再读 `docs/cli/01-cli-command-reference.md` |
| 服务 Action/离线目录 | `docs/components/17-action-catalog.md` |
| ExternalDB | `docs/components/11-externaldb.md`、`example/routes/MysqlRouteSrv/v1.0.0/` |
| 转换 | `skills/lightesb-transform-components/SKILL.md` |
| AI、SAP、工业协议 | 对应专项 skill 和组件文档 |

规则：

- 用户要求实际服务时，直接修改 `lightesb-camel-app/{serviceName}/{serviceVersion}`；演示、模板或 POC 才修改 `example/routes/**`。不在正式服务目录新增索引或说明文件。
- 新建服务最小集 = 路由 XML + `common.config.properties` + `service.config.properties`；版本目录使用 `vX.Y.Z`，`service.config.properties` 中的 `service.version` 使用不带 `v` 的 `X.Y.Z`；`log4j2.properties` 运行时自动生成，不要手工创建；Schema、samples 等只在路由实际使用时才添加。
- `<simple>` 体内不混用 `{{占位符}}` 与字面 `}}`（报 `Missing {{ from the text`）；占位符先经 `<constant>` 存入 exchangeProperty 再引用。simple 不支持 `? :` 三元表达式，条件取值用 `<choice>` + `<constant>`。
- HTTP 入站用 `<from uri="undertow:http://0.0.0.0:{{server.port}}/..."/>`。
- 入口放 `requestCharsetProcessor`，出口放 `jsonResponseProcessor`。
- 关键节点使用 `servicelog:`。
- 内部 HTTP 调用优先用 `127.0.0.1:{{server.port}}`、`bridgeEndpoint=true` 和明确超时。
- 内部 HTTP 调用后如果继续处理响应正文，按需 `<convertBodyTo type="java.lang.String"/>`；入口和子路由同名 path header 应先存到 Exchange Property 并 `removeHeader`，避免 Header 多值化。
- 无 HTTP 入口的定时任务使用 `timer:`，配置 `HTTP.Listener=false`。默认仅检查 XML、配置和 route id；只有用户明确授权运行态验证时才查看周期日志。
- 自然语言要求输入、输出或回调 JSON 校验时，不自行生成 Schema。按服务关系调用 `message schema generate`，检查 warnings，再把返回路径写入对应位置的完整校验块。
- route XML 是校验唯一开关，不生成额外配置开关。普通本地开发直接编辑正式服务目录，自行修正明显静态问题，并在授权后单独验证 Watcher 热加载；这条流程不调用 apply。需要 Action 审批 lineage 时，用 `ai route prepare --out <new-candidate-dir> --yes` 从服务端 content 持久化基线新建非热加载候选，只编辑候选并用 `ai route validate` 做只读校验；`ai route apply --save-remote --yes` 仅在用户明确授权远程写入后调用。同一次变更只选一条流程；已批准会话期间的 live 变化仍会 `STALE`。apply 失败时保留候选并读取恢复诊断，不自动重试。
- Action 的唯一事实源是服务目录中的 `service.config.properties`、唯一 route XML 和 metadata 引用的 schema；metadata 放在目标 `<route>` 内、唯一 `<from>` 之前。HTTP JSON 入口用 `entry`，经 processor 标准化的 MQTT/OPC UA envelope 用 `normalized` 并声明准确 processor ref。consumer/scheduled 不可 agent-callable，写入/破坏性 Action 必须显式声明幂等、重试和审批语义。
- 修改 Action 后运行 `java -jar lightesb-cli.jar action validate --service-dir lightesb-camel-app/{serviceName}/{serviceVersion}`。批量索引使用 `action build --app-root lightesb-camel-app --out <服务目录外路径> --yes`；它是可删除重建的派生产物，不手工编辑、不放入正式服务目录。
- 现场运行配置已显式开启 `lightesb.action-catalog.enabled=true` 时，受管 schema 修改/删除/补回依赖服务目录热加载，不因该文件变更重启 LightESB。等待监听完成后，检查 route 仍为 `RUNNING` 且日志出现新 Action `generation/revision`；同时开启 Action security 时，可用 `action status/list/get` 验证受保护的只读快照。失败时确认 quarantine，恢复 schema 后确认自愈到新 generation。只读查询不提供 Action 执行授权。
- 按 `docs/components/16-route-static-preflight.md` 完成通用和场景配置闭包检查：服务目录只有一个 XML；route id 唯一；XML 可解析；两个 properties 含服务名/版本和所需组件开关；所有 `{{...}}` 占位符有同目录配置来源；`.ds`、固定 Schema 等引用资源存在；没有用户未要求的外部 endpoint、凭据或能力。
- 提交前运行交付包内的离线预检：`python3 skills/lightesb-route-authoring/scripts/route-static-preflight.py --service-dir lightesb-camel-app/{serviceName}/{serviceVersion} --profile {http|timer|transform|schema|externaldb|ai-agent|mqtt|opcua|modbus|sap-mock} --route-file {route.xml}`。按实际场景选 profile；它只检查静态配置闭包，不启动服务或访问外部系统。

验收：

- `common.config.properties` 有 `HTTP.Listener=true`、`server.port` 和 `system.components=undertowhttp`。
- XML 里没有硬编码生产端口或真实环境地址。
- 已完成 XML、properties、资源和占位符静态自检；未把该结果表述为真实加载或业务验证。
- curl 或 Timer 周期日志仅在用户明确授权运行态验证时执行，`routeId` 不冲突。
- 校验方向、消息 ID、固定 Schema 文件和 route 中的位置一致。
- 显式启用运行时 Action Catalog 且修改受管 schema 时，已用 route 状态和 Action generation/revision 日志证明同代发布；做失败恢复测试时已证明 quarantine 和补回自愈。
