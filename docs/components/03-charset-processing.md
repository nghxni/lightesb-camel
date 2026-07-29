# 字符编码处理

## 用途

字符处理器用于确定性地统一请求和响应编码，减少响应 Content-Type 缺失和字符串二次编码问题。

## 官方参考

- [Camel Processor](https://camel.apache.org/manual/processor.html)：`<process ref="..."/>` 调用处理器的通用模型。
- [Camel Registry](https://camel.apache.org/manual/registry.html)：路由中 `ref` 如何解析到运行时注册的 Bean。

## 可用 Bean

| Bean | 用途 |
| --- | --- |
| `requestCharsetProcessor` | 请求侧 UTF-8 处理；字符串默认原样保留 |
| `responseCharsetProcessor` | 响应侧字符集统一 |
| `jsonResponseProcessor` | 响应体转 UTF-8 字节并自动识别 JSON/XML/HTML/文本 |
| `charsetProcessor` | 按明确阶段标记选择请求或响应处理 |

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
- AUTO 模式只在 `exchangeProperty.isResponsePhase=true` 时进入响应处理，不根据请求 `Content-Type` 猜测。
- 复杂路由不建议依赖 AUTO，显式写请求和响应处理器更清楚。

## 历史乱码兼容

默认行为：

- `String` 原样保留，不按字符特征猜测编码。
- `byte[]` 确定性按 UTF-8 解码。

仅当服务确实接收过被错误按 ISO-8859-1 解码的历史字符串时，在该服务版本的
`service.config.properties` 中显式设置：

```properties
charset.legacy-mojibake-repair.enabled=true
```

该开关会影响同服务的 CharsetProcessor 和内置转换回退。新服务不要把它作为
常规配置。

## 常见问题

- 中文仍乱码：先确认上游发送的字节编码和 `Content-Type`，再确认入口是否执行 `requestCharsetProcessor`；不要直接开启兼容开关掩盖上游错误。
- 下游不接受 `byte[]`：把 `jsonResponseProcessor` 换成 `responseCharsetProcessor`。
- Content-Type 不符合预期：优先使用 `jsonResponseProcessor` 自动识别。
