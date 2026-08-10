# example 样例索引

`example/` 是纯演示目录，可以修改服务名、端口、接口路径和数据。需要运行时，把完整样例服务目录复制到 `lightesb-camel-app/`，演示完成后删除。

## 样例目录

| 目录 | 用途 | 关联文档 |
| --- | --- | --- |
| `routes/http-undertow/DemoHttpSrv/v1.0.0/` | HTTP 入口、编码、servicelog | `../docs/components/01-http-route-basics.md` |
| `routes/HttpRequestSrv/v1.0.0/` | HTTP 入站后调用同服务内部 HTTP 子路由，默认端口 `18083` | `../docs/components/01-http-route-basics.md` |
| `routes/transform-json/DemoTransformSrv/v1.0.0/` | JSON 转换和 conditionaltransform 调用位置 | `../docs/components/04-transform-components.md` |
| `routes/PlatformHttp/v1.0.0/` | DataSonnet import、conditionaltransform、DTS/commonFunctions 转换演示，默认端口 `18081` | `../docs/components/04-transform-components.md` |
| `routes/PlatformHttp/v2.0.0/` | DTS/commonFunctions 独立 HTTP 演示，入口带服务版本路径，默认端口 `18081` | `../docs/components/04-transform-components.md` |
| `routes/PlatformHttp/v3.0.0/` | HTTP 订单转换、JSONPath 提取、servicelog 响应处理演示，默认端口 `18080` | `../docs/components/04-transform-components.md` |
| `routes/security-validation/DemoSecuritySrv/v1.0.0/` | JSON Schema 校验与 HTTP requestReply Action | `../docs/components/05-json-schema-validation.md`、`../docs/components/17-action-catalog.md` |
| `routes/logging-cache/DemoLogCacheSrv/v1.0.0/` | H2 缓存、JsonKeyword、StreamCache | `../docs/components/10-h2-jsonkeyword-chain.md` |
| `routes/timer/v1.0.0/` | Timer XML 片段样例，10 秒/15 秒日志触发 | `../docs/components/14-timer-routes.md` |
| `routes/timer/v1.0.1/` | Timer 服务级日志样例，包含配置文件，`HTTP.Listener=false` | `../docs/components/14-timer-routes.md` |
| `routes/MysqlRouteSrv/v1.0.0/` | ExternalDB MySQL 定时健康检查和 SQL 增删查删演示 | `../docs/components/11-externaldb.md` |
| `routes/AiAgentDemoSrv/v1.0.0/` | AI Agent + Tools 工具编排演示 | `../docs/components/12-ai-chat.md` |
| `routes/AvevaOpcUaSrv/v1.0.0/` | AVEVA OPC UA 遥测 Action（normalized、不可调用）和固定点位写控制样例，默认 `server.running=false` | `../docs/components/15-aveva-plant-scada-opcua-mqtt.md`、`../docs/components/17-action-catalog.md` |
| `routes/AvevaMqttSrv/v1.0.0/` | AVEVA MQTT 5 遥测 Action（normalized、不可调用）和固定命令 topic 发布样例，默认 `server.running=false` | `../docs/components/15-aveva-plant-scada-opcua-mqtt.md`、`../docs/components/17-action-catalog.md` |
| `routes/RobotMqttTelemetrySrv/v1.0.0/` | 机器人 MQTT telemetry 标准化 mock 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotMqttCommandSrv/v1.0.0/` | 机器人 HTTP/外部命令到 MQTT command envelope 的 mock 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotRosBridgeSrv/v1.0.0/` | rosbridge JSON 和机器人动作映射 mock 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotOpcUaStationSrv/v1.0.0/` | OPC UA 工作站读写边界和工业告警 mock 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotModbusGatewaySrv/v1.0.0/` | Modbus 寄存器别名白名单和写回执 mock 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotClusterDataSrv/v1.0.0/` | Kafka 风格出流、外部任务和 dashboard 数据 mock 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotGrpcGatewaySrv/v1.0.0/` | gRPC IDL 契约、deadline/retry/metadata/TLS 静态配置和 mock receipt 样例，默认 `server.running=false` | `../docs/experience/01-robotics-protocol-precheck.md` |
| `routes/RobotVda5050Srv/v1.0.0/` | VDA 5050 order/instantActions 命令校验、幂等和 envelope 构造 mock 样例，默认 `server.running=false` | `../docs/robot-command-dispatcher-api.md` |
| `routes/RobotEdgeInferenceSrv/v1.0.0/` | 边缘 AI 推理身份、时效、置信度、replay 与共享安全策略 mock 门禁，默认 `server.running=false` | `../docs/robot-edge-inference-mock.md` |
| `transform-dts-java/` | DTS Java SPI 扩展示例，提供多个 transform provider | `../docs/extensions/01-dts-extension-guide.md` |

## 运行方式

```bash
cp -R example/routes/http-undertow/DemoHttpSrv lightesb-camel-app/
./start.sh
curl -i "http://localhost:18080/api/demo/hello"
rm -rf lightesb-camel-app/DemoHttpSrv
```

PlatformHttp 转换演示：

```bash
cp -R example/routes/PlatformHttp lightesb-camel-app/
./start.sh
curl -X POST "http://localhost:18080/api/transform/order" \
  -H "Content-Type: application/json" \
  -d '{"orderId":"ORD-1001","customer":{"name":"张三"},"items":[{"sku":"SKU-001","qty":1}]}'
rm -rf lightesb-camel-app/PlatformHttp
```

PlatformHttp v1.0.0 复杂转换演示：

```bash
curl -X POST "http://localhost:18081/api/transform/complex-order" \
  -H "Content-Type: application/json" \
  -d @example/routes/PlatformHttp/v1.0.0/test.json

curl -X POST "http://localhost:18081/api/demo" \
  -H "Content-Type: application/json" \
  -d @example/routes/PlatformHttp/v1.0.0/test.json
```

PlatformHttp v2.0.0 DTS 演示：

```bash
curl -X POST "http://localhost:18081/2.0.0/api/demo" \
  -H "Content-Type: application/json" \
  -d @example/routes/PlatformHttp/v2.0.0/test.json
```

HttpRequestSrv 内部 HTTP 调用演示：

```bash
cp -R example/routes/HttpRequestSrv lightesb-camel-app/
./start.sh
curl -X POST "http://localhost:18083/api/httprequest/test" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
rm -rf lightesb-camel-app/HttpRequestSrv
```

Timer 演示：

```bash
mkdir -p lightesb-camel-app/TimerSrv
cp -R example/routes/timer/v1.0.1 lightesb-camel-app/TimerSrv/
./start.sh
# 观察 timer 路由日志；v1.0.1 每 30 秒有数据处理日志。
rm -rf lightesb-camel-app/TimerSrv
```

MysqlRouteSrv 演示：

```bash
cp -R example/routes/MysqlRouteSrv lightesb-camel-app/
# 先替换 service.config.properties 中的 PLACEHOLDER_CONFIGURE_IN_SITE，
# 准备 testexdb 表，再把 common.config.properties 的 server.running 改为 true。
./start.sh
# 观察 mysql-healthcheck-route 定时日志。
rm -rf lightesb-camel-app/MysqlRouteSrv
```

DTS Java 扩展示例：

```bash
cd example/transform-dts-java
mvn package
```

AI Agent 演示：

```bash
cp -R example/routes/AiAgentDemoSrv lightesb-camel-app/
./start.sh
curl -X POST "http://localhost:19095/api/ai/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"demo-order-session","message":"查询订单 MOCK-1001 的状态"}'
rm -rf lightesb-camel-app/AiAgentDemoSrv
```

临时审批表单演示（路由自吐 HTML 页面，mock 数据无持久化，删除路由 XML 即销毁）：

```bash
cp -R example/routes/TempApprovalMockSrv lightesb-camel-app/
./start.sh
# 浏览器打开表单页：http://127.0.0.1:19097/api/temp-approval/form
curl -X POST "http://127.0.0.1:19097/api/temp-approval/submit" \
  -H "Content-Type: application/json" \
  -d '{"title":"办公用品采购","applicant":"张三","amount":1000,"reason":"采购打印纸"}'
curl "http://127.0.0.1:19097/api/temp-approval/view?approvalId=MOCK-1"
curl -X POST "http://127.0.0.1:19097/api/temp-approval/approve" \
  -H "Content-Type: application/json" \
  -d '{"approvalId":"MOCK-1","action":"APPROVE","comment":"同意"}'
rm -rf lightesb-camel-app/TempApprovalMockSrv
```

AVEVA Plant SCADA OPC UA / MQTT 样例：

```bash
cp -R example/routes/AvevaOpcUaSrv lightesb-camel-app/
cp -R example/routes/AvevaMqttSrv lightesb-camel-app/
# 配置真实 Server/Broker、凭据和安全参数后，将对应 common.config.properties 的 server.running 改为 true。
./start.sh
curl -X POST "http://localhost:19110/api/aveva/opcua/write" \
  -H "Content-Type: application/json" \
  -d '{"value":55.5}'
curl -X POST "http://localhost:19111/api/aveva/mqtt/command" \
  -H "Content-Type: application/json" \
  -d '{"command":"start","deviceId":"Pump101"}'
rm -rf lightesb-camel-app/AvevaOpcUaSrv lightesb-camel-app/AvevaMqttSrv
```

机器人协议阶段 1-4 mock 样例：

```bash
cp -R example/routes/RobotMqttTelemetrySrv lightesb-camel-app/
cp -R example/routes/RobotMqttCommandSrv lightesb-camel-app/
# 样例默认 server.running=false；用于阅读和验证服务包结构、MQTT topic/clientId/QoS 契约，不会连接真实 broker 或机器人。
rm -rf lightesb-camel-app/RobotMqttTelemetrySrv lightesb-camel-app/RobotMqttCommandSrv
```

不要把索引文件复制到 `lightesb-camel-app/`。
需要发现上述样例中的 Action 时，复制完整服务目录后运行 `skills/lightesb-route-authoring/scripts/action-catalog.py --service-dir lightesb-camel-app/{serviceName}/v1.0.0`；派生输出写到服务目录外，完整规则见 `docs/components/17-action-catalog.md`。
`example/routes/**/log4j2.properties` 不需要随样例提供，运行时会自动生成。
