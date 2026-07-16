# JSON Schema 校验

## 用途

`jsonSchemaValidationProcessor` 用于在 Camel 路由中校验请求 JSON 结构。

当前实现使用 `com.networknt:json-schema-validator`，默认按 JSON Schema Draft 2020-12 校验。Schema 建议显式声明：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

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
- Draft 2020-12 关键字如 `prefixItems`、`unevaluatedProperties`、`additionalProperties` 需要纳入单元测试或路由回归。

## 消息体 Schema 预览

消息管理模块可从 `msgStructure` 生成 Draft 2020-12 JSON Schema：

| Endpoint | Method | 说明 |
| --- | --- | --- |
| `/message-management/v1/json-schema/preview` | POST | 使用请求体中的消息结构生成 schema |
| `/message-management/v1/json-schema/preview/{id}` | GET | 使用已保存消息生成 schema |

映射范围：`ROOT/ENTRY -> object`、`COLLECTION -> array`（优先第一个 `ENTRY` 子节点作为 `items`）、`VARCHAR2 -> string`、`REGEX.constraint -> pattern`、`INT -> integer`、`DATE -> date-time string`、`ifRequired == "1" -> required`。

当前不从 `constraint` 推导 `enum`；无法自洽映射的规则通过 `warnings` 返回。

CLI 可直接生成到对应服务版本目录：

```bash
lightesb message schema generate \
  --id <messageId> \
  --service-name DemoSrv \
  --service-version v1.0.0 \
  --schema-file request-schema.json \
  --yes --output json
```

也可将 `--id` 替换为 `--file message.json`，从尚未保存的消息定义生成。目标 `{app-dir}/{serviceName}/{serviceVersion}` 必须已存在。路由需要 JSON 校验且已有消息模型时，应先调用该命令、检查 warnings，再将返回的 `data.jsonSchemaPath` 写入 `JsonSchemaPath`；不要根据同一 `msgStructure` 手工维护第二份 Schema。
