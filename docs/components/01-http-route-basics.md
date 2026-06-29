# HTTP 入口与路由基础

## 用途

`undertow` 用于把 HTTP 请求接入 Camel XML 路由。交付包内新增接口时，优先参考 `example/routes/http-undertow/`，确认可运行后再复制到 `lightesb-camel-app/`。

相关样例：

- `example/routes/http-undertow/DemoHttpSrv/v1.0.0/`：最小 HTTP 入站。
- `example/routes/HttpRequestSrv/v1.0.0/`：HTTP 入站后调用同服务内部 HTTP 子路由，默认端口 `18083`。

## 最小配置

`common.config.properties`:

```properties
HTTP.Listener=true
server.port=18080
system.components=undertowhttp
```

`service.config.properties`:

```properties
service.name=DemoHttpSrv
service.version=v1.0.0
```

## 路由模板

```xml
<routes xmlns="http://camel.apache.org/schema/spring">
  <route id="demo-http-route">
    <from uri="undertow:http://0.0.0.0:{{server.port}}/api/demo/hello?httpMethodRestrict=GET,POST"/>
    <process ref="requestCharsetProcessor"/>
    <to uri="servicelog:info?message=收到请求 method=${header.CamelHttpMethod}&amp;showHeaders=false"/>
    <setHeader name="Content-Type"><constant>application/json; charset=UTF-8</constant></setHeader>
    <setBody><simple>{"code":"OK","path":"${header.CamelHttpPath}"}</simple></setBody>
    <process ref="jsonResponseProcessor"/>
    <to uri="servicelog:info?message=请求完成&amp;showBody=true&amp;maxBodyLength=500"/>
  </route>
</routes>
```

## 写法规则

- `undertow:http://...` 只能放在 `<from>`。
- 端口使用 `{{server.port}}`，不要在 XML 中硬编码。
- 用 `httpMethodRestrict=GET,POST` 显式限制方法。
- 入口建议先调用 `requestCharsetProcessor`，出口建议调用 `jsonResponseProcessor`。
- 关键节点用 `servicelog:` 记录，不要直接打印全量大报文。

## 跨域处理

如果接口会被浏览器页面调用，需要同时处理 CORS 预检请求和正常响应头。参考 `lightesb-camel-app/Doctor360Srv/v1.0.0/doctor360-route.xml`。

### OPTIONS 预检路由

```xml
<route id="demo-api-cors-preflight-route">
  <from uri="undertow:http://0.0.0.0:{{server.port}}/api/demo/items?httpMethodRestrict=OPTIONS&amp;matchOnUriPrefix=true"/>
  <setHeader name="Access-Control-Allow-Origin"><constant>*</constant></setHeader>
  <setHeader name="Access-Control-Allow-Methods"><constant>GET,POST,OPTIONS</constant></setHeader>
  <setHeader name="Access-Control-Allow-Headers"><constant>Content-Type,Authorization,X-Requested-With,Accept,Origin</constant></setHeader>
  <setHeader name="Access-Control-Max-Age"><constant>3600</constant></setHeader>
  <setHeader name="CamelHttpResponseCode"><constant>204</constant></setHeader>
  <setBody><constant></constant></setBody>
</route>
```

### 业务路由响应头

业务路由也要设置允许跨域的响应头，否则预检通过后浏览器仍可能拦截响应：

```xml
<setHeader name="Content-Type"><constant>application/json;charset=UTF-8</constant></setHeader>
<setHeader name="Access-Control-Allow-Origin"><constant>*</constant></setHeader>
<setHeader name="Access-Control-Allow-Methods"><constant>GET,POST,OPTIONS</constant></setHeader>
<setHeader name="Access-Control-Allow-Headers"><constant>Content-Type,Authorization,X-Requested-With,Accept,Origin</constant></setHeader>
```

写法要点：

- 预检路由用 `httpMethodRestrict=OPTIONS`。
- 多级路径或路径前缀匹配时加 `matchOnUriPrefix=true`。
- 预检成功建议返回 `204` 和空 body。
- 正常业务响应也要带 CORS 头。

## 调用 Camel 内部 HTTP 子路由

同一个服务中可以用 `toD` 调用本进程内的 HTTP 子路由，适合工具路由、mock 路由和内部编排。参考 `example/routes/AiAgentDemoSrv/v1.0.0/ai-agent-demo-route.xml` 中的 “调用内部 HTTP mock 子路由：bridgeEndpoint=true”。

调用方：

```xml
<setHeader name="CamelHttpMethod"><constant>GET</constant></setHeader>
<toD uri="http://127.0.0.1:{{server.port}}/api/demo/mock/${header.id}?bridgeEndpoint=true&amp;connectTimeout=5000&amp;socketTimeout=30000&amp;throwExceptionOnFailure=false"/>
```

设置下游 HTTP 方法时，XML DSL 必须使用 `CamelHttpMethod`。不要把 Java 常量名写进 XML header 名称：

```xml
<!-- 错误：会创建普通 header，HTTP producer 不一定按它设置请求方法 -->
<setHeader name="Exchange.HTTP_METHOD"><constant>POST</constant></setHeader>

<!-- 正确：Camel HTTP producer 识别该 header -->
<setHeader name="CamelHttpMethod"><constant>POST</constant></setHeader>
```

被调用子路由：

```xml
<route id="demo-mock-route">
  <from uri="undertow:http://0.0.0.0:{{server.port}}/api/demo/mock/{id}?httpMethodRestrict=GET"/>
  <setHeader name="Content-Type"><constant>application/json</constant></setHeader>
  <setHeader name="CamelHttpResponseCode"><constant>200</constant></setHeader>
  <setBody><simple>{"success":true,"id":"${header.id}"}</simple></setBody>
</route>
```

参数说明：

- `127.0.0.1:{{server.port}}`：调用当前服务监听端口，避免硬编码端口。
- `bridgeEndpoint=true`：按桥接方式调用内部 HTTP 端点，减少外部主机头等信息干扰。
- `throwExceptionOnFailure=false`：下游返回 4xx/5xx 时不直接抛异常，便于路由自行判断响应码和 body。
- `connectTimeout` / `socketTimeout`：内部调用也要设置超时，避免链路挂死。

`HttpRequestSrv` 演示了固定 URI 的内部 HTTP 调用：

```xml
<from uri="undertow:http://0.0.0.0:{{server.port}}/api/httprequest/test?httpMethodRestrict=POST" />
<to uri="http://0.0.0.0:18083/api/test?httpMethod=POST&amp;contentType=application/json&amp;bridgeEndpoint=true&amp;connectTimeout=5000&amp;socketTimeout=30000"/>
```

演示可直接调用：

```bash
curl -X POST "http://localhost:18083/api/httprequest/test" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
```

正式样例建议把内部调用地址改成 `127.0.0.1:{{server.port}}`，减少端口重复维护。

## 验证

```bash
curl -i "http://localhost:18080/api/demo/hello"
```

预期：

- HTTP 200。
- 响应 `Content-Type` 包含 `charset=UTF-8`。
- 服务日志能看到入口和出口日志。
- 跨域接口可用 `curl -i -X OPTIONS ...` 检查 `Access-Control-Allow-*` 响应头。

## 常见问题

- 端口不可访问：检查 `HTTP.Listener=true`、`server.port` 和端口占用。
- 405 或路由不执行：检查 `httpMethodRestrict` 是否包含当前方法。
- 中文乱码：确认入口和出口处理器是否已放入路由。
- 浏览器跨域失败：确认 OPTIONS 预检路由和业务响应都设置了 CORS 头。
- 内部 HTTP 子路由调用失败：确认被调用路由路径、方法限制和 `server.port` 一致。
