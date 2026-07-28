# 路由静态自检与配置闭包

在交付任何本地路由改动前，按本清单检查最终文件。它只提高 Q0-Q2 静态可加载置信度，不证明服务已加载（Q3）或业务已验证（Q4）。默认不启动 LightESB、不执行 curl、不连接外部系统。

## 通用闭包

1. 一个服务版本目录只保留一个 `*.xml`；route id 唯一。
2. XML 可解析；`common.config.properties`、`service.config.properties` 可解析，且有 `service.name`、`service.version`。
3. XML 中每个 `{{key}}` 都能在同目录两个 properties 找到；环境变量只能写成 `{{env:NAME}}`。
4. `.ds`、`request-schema.json`、`response-schema.json`、`callback-schema.json` 等实际引用资源与 XML 路径一致且文件存在；资源可位于当前服务目录，或使用以 `lightesb-camel-app/` 开头的仓库相对路径。
5. 不写真实凭据、生产地址或用户未要求的 endpoint/组件；修改已有服务时不重写无关 route。

可在交付包根目录运行确定性离线检查：

```bash
python3 skills/lightesb-route-authoring/scripts/route-static-preflight.py \
  --service-dir lightesb-camel-app/{serviceName}/{serviceVersion} \
  --profile externaldb \
  --route-file {route.xml}
```

`--profile` 可选 `http`、`timer`、`transform`、`schema`、`externaldb`、`ai-agent`、`mqtt`、`opcua`、`modbus`、`sap-mock`。工具检查 XML 唯一性、两个 properties、服务标识、XML 占位符、场景配置键/组件、默认启停值（例如工业协议 `server.running=false`）、已引用 `.ds`/JSON 资源和部分场景 endpoint；不读取环境变量实际值、不连接外部系统，也不替代加载或业务验证。

## 按场景的最小检查

| 场景 | 必需配置/文件 | XML 检查 | 权威资料 |
| --- | --- | --- | --- |
| HTTP | `HTTP.Listener=true`、`server.port`、`system.components=undertowhttp` | `undertow:http://0.0.0.0:{{server.port}}`，入口字符集和 JSON 响应处理器按需求使用 | [HTTP 基础](01-http-route-basics.md)、`example/routes/http-undertow/` |
| Timer | `HTTP.Listener=false` | `timer:` URI 的周期明确，route id 唯一 | [Timer](14-timer-routes.md)、`example/routes/timer/v1.0.1/` |
| DataSonnet/转换 | HTTP 场景再加 `system.components` 中的 `jsontransform,conditionaltransform`、`input-transform=true`、`input-transform.file=<文件>` | `conditionaltransform:input` 或明确的转换 endpoint；`.ds` 文件存在 | [转换](04-transform-components.md)、`example/routes/transform-json/` |
| JSON Schema | HTTP 配置；固定 Schema 文件 | `JsonSchemaPath`、`JsonSchemaValidationMode` 和 `jsonSchemaValidationProcessor` 成对存在 | [Schema](05-json-schema-validation.md)、`example/routes/security-validation/` |
| ExternalDB | `HTTP.Listener=false`（仅健康检查时）、`system.components=externaldb`、`extdb.enabled`、`extdb.default`、`extdb.ids`、`extdb.primary.{type,url,driver,username,password}` | `sql:` 使用 `#bean:extdb-{{extdb.default}}-datasource`；只读需求不得含写 SQL | [ExternalDB](11-externaldb.md)、`example/routes/MysqlRouteSrv/v1.0.0/` |
| AI Agent + Tool | HTTP 配置；`service.ai.route`、`service.ai.type`、`service.ai.mode=agent`、`ai.agent.tags` | `langchain4j-agent` 与 `langchain4j-tools` 标签一致；工具默认 mock-only | [AI Agent](12-ai-chat.md)、`example/routes/AiAgentDemoSrv/v1.0.0/` |
| MQTT 5 | `system.components` 含 `industrial`、`HTTP.Listener=false`、`server.running=false`、`industrial.mqtt.{broker.url,client.id,telemetry.topic,qos,username,password}` | `paho-mqtt5:{{industrial.mqtt.telemetry.topic}}`，并带固定 `brokerUrl`、`clientId`、`qos` 占位符；不把动态 topic/endpoint 暴露给请求体 | [工业协议](15-aveva-plant-scada-opcua-mqtt.md)、`example/routes/AvevaMqttSrv/` |
| OPC UA | `system.components` 含 `industrial`、`HTTP.Listener=false`、`server.running=false`、`industrial.opcua.{endpoint.uri,client.id,read.node,username,password,security}` | `milo-client:{{industrial.opcua.endpoint.uri}}?node={{industrial.opcua.read.node}}&amp;clientId={{industrial.opcua.client.id}}-reader`；不把动态 node/endpoint 暴露给请求体 | [工业协议](15-aveva-plant-scada-opcua-mqtt.md)、`example/routes/AvevaOpcUaSrv/` |
| Modbus TCP（PLC4X） | `HTTP.Listener=false`、`system.components=industrial`、`server.running=false`、`industrial.modbus.connection`、`.read.tag`、`.polling.ms` | `plc4x:{{industrial.modbus.connection}}?tag.<alias>={{industrial.modbus.read.tag}}&amp;period={{industrial.modbus.polling.ms}}`；只读模板不得含写 endpoint | [工业协议](15-aveva-plant-scada-opcua-mqtt.md) |
| SAP 无现场环境 | HTTP 配置 | 仅 HTTP mock；动态 endpoint/username/password 返回明确拒绝；不使用 `sap-netweaver:` | [SAP](13-sap-netweaver.md) |

## 交付说明

列出修改文件和已执行的静态检查，明确尚未验证的加载、外部连接和业务结果，并给出用户可执行的最小手工验证入口。只有用户明确授权时，才执行 runtime、curl、远程 apply 或外部连接验证。
