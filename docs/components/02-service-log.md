# 服务日志 servicelog

## 用途

`servicelog:` 是服务级日志组件，用于在路由中记录关键节点、请求摘要、响应摘要和异常信息。

## URI

```text
servicelog:level?message=...&showBody=false&showHeaders=false&maxBodyLength=1000
```

`level` 可用：`trace`、`debug`、`info`、`warn`、`error`。

## 常用参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `message` | 空 | 日志消息，支持 Camel Simple 表达式 |
| `showBody` | `false` | 是否输出消息体 |
| `showHeaders` | `false` | 是否输出消息头 |
| `maxBodyLength` | `1000` | 最大消息体长度 |
| `useStream` | `false` | 大报文摘要模式 |
| `showBodySummary` | `true` | 大报文时输出摘要 |

## 样例

```xml
<to uri="servicelog:info?message=收到请求 service=${exchangeProperty.serviceName}"/>
<to uri="servicelog:info?message=处理完成&amp;showBody=true&amp;maxBodyLength=1000"/>
<to uri="servicelog:warn?message=校验失败 ${exception.message}"/>
```

运行时可用 Exchange 属性覆盖长度：

```xml
<setProperty name="servicelog.maxBodyLength"><constant>5000</constant></setProperty>
<to uri="servicelog:debug?message=排障输出&amp;showBody=true"/>
```

## 写入前脱敏

在服务版本配置中显式开启：

```properties
log.redaction.enabled=true
log.redaction.additional-fields=customerPin,partnerCredential
log.redaction.max-input-chars=1048576
```

开启后，`servicelog` message/body/header/异常、DEBUG 输出和 H2/MySQL 实例日志在写入前使用同一字段策略；password、secret、token、authorization、cookie、apiKey 和 credential 等默认字段会被替换。默认关闭以保留既有行为。

需要查看原文时，只能在受控本地测试服务临时关闭总开关并等待配置热加载。不要把读取权限理解为脱敏开关：关闭后任何有日志读取权限的人都可能看到原文；开启后读取者只能看到已脱敏值。历史日志不会自动回填，普通 Camel `log:` 和第三方日志也不在此服务级门禁范围内。

## 建议

- `info` 记录入口、出口和关键业务节点。
- `warn` 记录可恢复问题。
- `error` 记录异常链路。
- 大报文只在排障时打开 `showBody=true`，并控制 `maxBodyLength`。

## 验证

- 请求接口后检查服务目录下的 `logs/`。
- 动态排障时优先查看服务日志中的最新记录和 `DEBUG.log`。

## 重新读取日志配置

按 route `fileKey` 重载：

```bash
curl -X POST \
  "http://127.0.0.1:8080/api/logging/reload/PlatformHttp@v3.0.0@platform-http-route.xml"
```

按服务版本重载全部已加载 route logger：

```bash
curl -X POST \
  "http://127.0.0.1:8080/api/logging/reload/PlatformHttp@v3.0.0"
```

兼容入口：

```bash
curl -X POST \
  "http://127.0.0.1:8080/api/lightesb/config/logging/reconfigure/PlatformHttp/v3.0.0"
```

接口使用运行时服务配置重新读取服务版本目录并重建 logger，同时清除对应健康
缓存。服务或 fileKey 未加载时返回 `SERVICE_LOG_CONFIG_NOT_FOUND`，不会返回
伪成功。成功后应发送一条业务请求并检查服务版本目录下的 `logs/`。
