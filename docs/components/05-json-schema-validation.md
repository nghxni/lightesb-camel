# JSON Schema 校验

## 用途

`jsonSchemaValidationProcessor` 用于在 Camel 路由中校验请求 JSON 结构。

## 使用方式

```xml
<setProperty name="JsonSchemaPath"><constant>example/routes/security-validation/order-schema.json</constant></setProperty>
<setProperty name="JsonSchemaValidationMode"><constant>STRICT</constant></setProperty>
<process ref="jsonSchemaValidationProcessor"/>
```

## Exchange 属性

| 属性 | 说明 |
| --- | --- |
| `JsonSchemaContent` | Schema 字符串，优先级最高 |
| `JsonSchemaPath` | Schema 文件路径或 classpath 路径 |
| `JsonSchemaId` | 标识和缓存辅助，不能单独完成校验 |
| `JsonSchemaValidationMode` | `STRICT`、`LENIENT`、`SKIP` |

## 模式

- `STRICT`：默认，失败抛错，适合强校验。
- `LENIENT`：失败不中断，写入 `X-Validation-Warnings`。
- `SKIP`：跳过校验，适合临时联调。

## 失败处理建议

```xml
<doTry>
  <process ref="jsonSchemaValidationProcessor"/>
  <doCatch>
    <exception>java.lang.Exception</exception>
    <setHeader name="CamelHttpResponseCode"><constant>400</constant></setHeader>
    <setBody><simple>{"error":"VALIDATION_ERROR","message":"${exception.message}"}</simple></setBody>
  </doCatch>
</doTry>
```

## 验证

- 合法 JSON 在 `STRICT` 下通过。
- 非法 JSON 在 `STRICT` 下返回 400 或进入全局异常响应。
- `LENIENT` 下流程继续，响应或日志包含告警信息。
