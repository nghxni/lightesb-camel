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
| `CALLBACK` | 当前服务固定的 `serviceCallbackMessageId` | `callback-schema.json` | 调用回调服务前 |

`serviceCallbackId` 是回调服务 ID，不是消息 ID。使用当前服务固定的 `serviceCallbackMessageId/serviceCallbackInRevision/serviceCallbackInModelDigest`，不能读取目标最新消息代替固定快照。三个 Schema 都写入当前服务版本目录。

## 使用方式

```xml
<setProperty name="JsonSchemaPath"><constant>request-schema.json</constant></setProperty>
<setProperty name="JsonSchemaValidationMode"><constant>STRICT</constant></setProperty>
<removeProperty name="JsonSchemaContent"/>
<process ref="jsonSchemaValidationProcessor"/>
```

OUTPUT 和 CALLBACK 使用同一完整校验块，只替换为 `response-schema.json` 或 `callback-schema.json`，并放到上表指定位置。route XML 是校验是否启用的唯一事实：需要就加入完整块，草稿不需要时删除完整块及未使用的受管文件/来源；冻结后改变受管引用或模式须新建服务版本；不要新增全局、服务配置或数据库开关，也不要用 `SKIP` 充当业务开关。

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

## 固定消息修订与 Schema 预览

消息管理模块可从 `msgStructure` 生成 Draft 2020-12 JSON Schema：

| Endpoint | Method | 说明 |
| --- | --- | --- |
| `/message-management/v1/json-schema/preview` | POST | 使用请求体中的消息结构生成 schema |
| `/message-management/v1/revisions/{id}/{revision}/json-schema` | GET | 从精确修订正式生成，可选 expectedModelDigest |
| `/message-management/v1/json-schema/preview/{id}` | GET | 仅预览当前消息 |

ROOT 是 XML 根容器，JSON/Schema 直接包含其子字段；ENTRY 为对象，COLLECTION 恰好一个 item，可为任意非 ROOT 类型。VARCHAR2/REGEX/DATE 为字符串，DATE 启用 date-time 格式断言；INT/NUMBER/BOOLEAN/NULL 保留原生类型。ifRequired 控制对象属性存在，nullable 单独控制 null。alias 为 null/缺省才使用 nodeName，空串是精确 JSON 键。

nodeLength/minLength 控制字符串长度，minimum/maximum 为精确数字文本。enumValues 为非空 JSON 数组文本；defaultValue 为严格 JSON 值文本，null 字段代表未设置，文本 null/""/0/false 区分显式 null、空串、数字和布尔。默认值与枚举均校验类型及约束；未知类型和无法表达的 constraint 明确拒绝。

CLI 可直接生成到对应服务版本目录：

```bash
lightesb message schema generate \
  --id <messageId> --revision <revisionId> --expected-model-digest <modelDigest> \
  --service-name DemoSrv \
  --service-version v1.0.0 \
  --schema-file request-schema.json \
  --yes --output json
```

预览时将 `--id --revision --expected-model-digest` 替换为 `--file message.json`，同时改用 `--schema-file preview-schema.json`，从尚未保存的消息定义预览，返回 preview=true，无持久修订身份。目标 `{app-dir}/{serviceName}/{serviceVersion}` 必须已存在。

CLI 核对选定身份以及 schemaContent 的 SHA-256 与 schemaDigest 后，按 UTF-8 原样写出权威文本，不重新排版或追加换行。正式响应附修订、模型与快照摘要，预览不能冒充绑定契约。Schema 内容只能使用接口返回的 `data.schemaContent`，不得由模型根据 `msgStructure` 自行生成、补写或修改。生成命令会连接服务端并写本地文件，需符合当前任务授权。正式来源必须无 warnings，预览不能作为受管文件；将 `data.jsonSchemaPath` 原样写入路由。

Schema 来源不决定路由的修改通道：普通本地开发直接编辑目标服务目录并做静态检查，运行态验证按授权单独执行，不调用 apply。远程保存或审批会话受管变更先准备非热加载候选，明确授权远程写入后才用 `lightesb ai route apply --save-remote --yes` 一次提交 route、properties 和实际引用的固定 Schema；不能先改 live 再用旧 session 追认。冻结后增删受管校验块、模式或 Action 方向须新建服务版本。

### 受管发布的固定来源

先创建服务定义并绑定消息 ID/revision/modelDigest。CLI 正式生成三个固定文件时同步写入 service.config.properties 的 lightesb.contract.<direction>.* 来源，须随候选一起提交；不要覆盖或手工伪造这些属性。草稿目录已有 XML 时改用独立候选目录，冻结版本只允许恢复相同 Schema 摘要与生成器的受管文件。预览只写无 XML 目录的自定义文件，不写正式来源。来源属性不充当运行时校验开关；普通自定义或内联 Schema 的处理器用法仍按本组件说明执行。
