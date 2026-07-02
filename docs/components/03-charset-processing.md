# 字符编码处理

## 用途

字符处理器用于统一请求和响应编码，减少中文乱码、响应 Content-Type 缺失和字符串二次编码问题。

## 官方参考

- [Camel Processor](https://camel.apache.org/manual/processor.html)：`<process ref="..."/>` 调用处理器的通用模型。
- [Camel Registry](https://camel.apache.org/manual/registry.html)：路由中 `ref` 如何解析到运行时注册的 Bean。

## 可用 Bean

| Bean | 用途 |
| --- | --- |
| `requestCharsetProcessor` | 请求侧 UTF-8 修复 |
| `responseCharsetProcessor` | 响应侧字符集统一 |
| `jsonResponseProcessor` | 响应体转 UTF-8 字节并自动识别 JSON/XML/HTML/文本 |
| `charsetProcessor` | 自动判断请求或响应阶段 |

## 推荐编排

```xml
<from uri="undertow:http://0.0.0.0:{{server.port}}/api/demo?httpMethodRestrict=POST"/>
<process ref="requestCharsetProcessor"/>
<!-- 业务处理 -->
<process ref="jsonResponseProcessor"/>
```

## 选择建议

- HTTP 入站后：使用 `requestCharsetProcessor`。
- 返回 JSON/XML/HTML/文本：使用 `jsonResponseProcessor`。
- 已经明确只返回 JSON 且不希望 body 变成 `byte[]`：可用 `responseCharsetProcessor`。
- 复杂路由不建议依赖自动判断，显式写请求和响应处理器更清楚。

## 常见问题

- 中文仍乱码：确认入口是否先执行 `requestCharsetProcessor`。
- 下游不接受 `byte[]`：把 `jsonResponseProcessor` 换成 `responseCharsetProcessor`。
- Content-Type 不符合预期：优先使用 `jsonResponseProcessor` 自动识别。
