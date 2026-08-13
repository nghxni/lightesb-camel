# JSON Schema 校验

## 用途

`jsonSchemaValidationProcessor` 用于在 Camel 路由中校验输入、输出或回调 JSON 结构。

当前实现使用 `com.networknt:json-schema-validator`，默认按 JSON Schema Draft 2020-12 校验。Schema 建议显式声明：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

## 三个校验方向

已有消息模型时，先查询当前服务关系，再按方向选择消息和固定文件：

| 方向 | 消息 ID | 固定文件 | 校验位置 |
| --- | --- | --- | --- |
| `INPUT` | 当前服务的 `serviceInId` | `request-schema.json` | 入站后、业务处理前 |
| `OUTPUT` | 当前服务的 `serviceOutId` | `response-schema.json` | 响应返回前 |
| `CALLBACK` | 回调服务的 `serviceInId` | `callback-schema.json` | 调用回调服务前 |

`serviceCallbackId` 是回调服务 ID，不是消息 ID。必须先用它查询回调服务，再读取回调服务的 `serviceInId`。三个 Schema 都写入当前服务版本目录。

## 使用方式

```xml
<setProperty name="JsonSchemaPath"><constant>request-schema.json</constant></setProperty>
<setProperty name="JsonSchemaValidationMode"><constant>STRICT</constant></setProperty>
<process ref="jsonSchemaValidationProcessor"/>
```

OUTPUT 和 CALLBACK 使用同一完整校验块，只替换为 `response-schema.json` 或 `callback-schema.json`，并放到上表指定位置。route XML 是校验是否启用的唯一事实：需要就加入完整块，不需要就删除完整块；不要新增全局、服务配置或数据库开关，也不要用 `SKIP` 充当业务开关。

相对路径统一以当前 `serviceName/serviceVersion` 目录为基准，同目录资源只写文件名，子目录资源写 `schemas/name.json`。绝对路径保持原含义；不要再把 `lightesb-camel-app/{serviceName}/{serviceVersion}/...` 作为工作目录相对前缀写入路由。

## Exchange 属性

| 属性 | 说明 |
| --- | --- |
| `JsonSchemaContent` | Schema 字符串，优先级最高 |
| `JsonSchemaPath` | 相对当前服务版本目录的 Schema 路径、绝对文件路径或显式 `classpath:` 路径 |
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

`example/routes/security-validation/DemoSecuritySrv/v1.0.0/` 还声明了 `demo-security-check` Action：`order-schema.json` 是 entry 输入契约，`response-schema.json` 是同步成功响应契约。二者由 route metadata 显式引用；Action 离线派生方法见 [服务 Action 声明与离线索引](17-action-catalog.md)。

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

也可将 `--id` 替换为 `--file message.json`，从尚未保存的消息定义生成。目标 `{app-dir}/{serviceName}/{serviceVersion}` 必须已存在。

Schema 内容只能使用接口返回的 `data.schema`，不得由模型根据 `msgStructure` 自行生成、补写或修改。`data.warnings` 非空时停止自动 apply，展示完整 warnings，只有用户明确确认后才能继续。将 `data.jsonSchemaPath` 原样写入路由；用户审核 route、properties 和 Schema 候选后，使用 `lightesb ai route apply --save-remote --yes` 一次提交路由实际引用的固定 Schema。删除某方向校验块后重新 apply 会删除对应受管固定 Schema，不影响自定义 Schema。
