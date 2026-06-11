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
| `routes/security-validation/DemoSecuritySrv/v1.0.0/` | JSON Schema 和权限校验编排 | `../docs/components/05-json-schema-validation.md` |
| `routes/logging-cache/DemoLogCacheSrv/v1.0.0/` | H2 缓存、JsonKeyword、StreamCache | `../docs/components/10-h2-jsonkeyword-chain.md` |
| `routes/timer/v1.0.0/` | Timer XML 片段样例，10 秒/15 秒日志触发 | `../docs/components/14-timer-routes.md` |
| `routes/timer/v1.0.1/` | Timer 服务级日志样例，包含配置文件，`HTTP.Listener=false` | `../docs/components/14-timer-routes.md` |
| `routes/MysqlRouteSrv/v1.0.0/` | ExternalDB MySQL 定时健康检查和 SQL 增删查删演示 | `../docs/components/11-externaldb.md` |
| `routes/AiAgentDemoSrv/v1.0.0/` | AI Agent + Tools 工具编排演示 | `../docs/components/12-ai-chat.md` |
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
./start.sh
# 准备 MySQL 连接配置和 testexdb 表后，观察 mysql-healthcheck-route 定时日志。
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

不要把索引文件复制到 `lightesb-camel-app/`。
`example/routes/**/log4j2.properties` 不需要随样例提供，运行时会自动生成。
