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

## 建议

- `info` 记录入口、出口和关键业务节点。
- `warn` 记录可恢复问题。
- `error` 记录异常链路。
- 大报文只在排障时打开 `showBody=true`，并控制 `maxBodyLength`。

## 验证

- 请求接口后检查服务目录下的 `logs/`。
- 动态排障时优先查看服务日志中的最新记录和 `DEBUG.log`。
