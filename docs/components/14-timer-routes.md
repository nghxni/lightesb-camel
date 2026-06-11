# Timer 定时路由

## 用途

`timer:` 用于不依赖 HTTP 入口的周期性任务，例如健康检查、定时同步、后台数据处理和日志自检。

## 样例

- `example/routes/timer/v1.0.0/`：纯 XML 片段样例，演示独立 CamelContext 下两个定时路由。
- `example/routes/timer/v1.0.1/`：带 `common.config.properties` 和 `service.config.properties` 的服务级日志样例，`HTTP.Listener=false`。
- `example/routes/MysqlRouteSrv/v1.0.0/`：`timer:` + `externaldb` + `sql:` 的 MySQL 健康检查和增删查删演示。

## 最小写法

```xml
<route id="demo-timer-route">
  <from uri="timer:demoTimer?period=30000"/>
  <setBody>
    <simple>{"status":"ACTIVE","timestamp":"${date:now:yyyy-MM-dd HH:mm:ss}"}</simple>
  </setBody>
  <to uri="servicelog:info?message=定时任务完成&amp;showBody=true"/>
</route>
```

配置要点：

```properties
HTTP.Listener=false
```

如果路由中使用 `servicelog:`、`jsonResponseProcessor`、`externaldb` 等能力，仍然要按对应组件文档启用配置和准备前置资源。

## 周期参数

| 参数 | 说明 |
| --- | --- |
| `period` | 触发周期，单位毫秒 |
| `fixedRate` | 是否按固定频率触发，常用于健康检查 |

示例：

```xml
<from uri="timer:statusCheck?period=15000"/>
<from uri="timer://mysql-healthcheck?fixedRate=true&amp;period=60000"/>
```

## 验收

- 启动后不需要 curl，观察服务日志或 Camel 标准日志。
- 确认 `routeId` 唯一，周期符合预期。
- 长周期任务可以临时把 `period` 调小做演示，完成后恢复。
- 访问数据库、外部 HTTP 或文件系统的定时任务要有异常分支，避免一次失败造成日志不可定位。

## 常见问题

- 没有 HTTP 入口：这是定时路由的正常形态，配置 `HTTP.Listener=false` 即可。
- 启动后看不到结果：检查 `period` 是否过长，以及日志级别是否允许输出。
- 复制 `timer/v1.0.0` 运行失败：该目录是 XML 片段样例；需要完整服务目录时参考 `timer/v1.0.1` 补齐配置文件。
