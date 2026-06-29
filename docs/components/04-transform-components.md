# 条件转换与 JSON 转换

## 组件

- `conditionaltransform`：按输入、输出或自定义转换文件执行可选转换。
- `jsontransform`：按配置 ID 执行 JSON 规则映射。

## 启用

`common.config.properties`:

```properties
system.components=undertowhttp,conditionaltransform,jsontransform
```

综合样例：

- `example/routes/PlatformHttp/v1.0.0/`：DataSonnet import、`conditionaltransform:input`、DTS/commonFunctions 组合演示，默认端口 `18081`。
- `example/routes/PlatformHttp/v2.0.0/`：DTS/commonFunctions 独立 HTTP 演示，入口为 `/2.0.0/api/demo`，默认端口 `18081`。
- `example/routes/PlatformHttp/v3.0.0/`：HTTP 订单转换、JSONPath 字段提取、servicelog 响应处理演示，默认端口 `18080`。
- `example/routes/transform-json/DemoTransformSrv/v1.0.0/`：最小转换路由骨架。

## conditionaltransform

URI:

```text
conditionaltransform:type?file=...&required=false&skipOnError=true
```

| 参数 | 说明 |
| --- | --- |
| `type` | `input`、`output`、`custom` |
| `file` | 自定义转换文件名，常配合 `custom` |
| `required` | 失败时是否必须抛错 |
| `skipOnError` | 失败后是否跳过继续处理 |

样例：

```xml
<to uri="conditionaltransform:input?skipOnError=true"/>
<to uri="conditionaltransform:custom?file=input-transform.ds&amp;required=true"/>
```

DataSonnet import 样例可参考 `example/routes/PlatformHttp/v1.0.0/input-transform-with-import.ds` 和同目录 `DATASONNET_IMPORT_GUIDE.md`。

服务配置中启用：

```properties
input-transform=true
input-transform.file=input-transform-with-import.ds
system.components=undertowhttp,streamcache,jsontransform,conditionaltransform
```

`system.components` 属于通用运行配置；`input-transform*`、`output-transform*` 等转换开关属于服务私有能力配置。通过 AI 路由生成时，只有自然语言明确要求输入转换、输出转换、字段映射或 `.ds` 资源时，才应生成这些转换键；默认能力枚举不代表自动启用转换。

对应入口：

```text
POST /api/transform/complex-order
```

## jsontransform

URI:

```text
jsontransform:configId?strictMode=false&failOnError=true
```

常用参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `cacheEnabled` | `true` | 缓存转换配置 |
| `strictMode` | `false` | 严格模式 |
| `failOnError` | `true` | 失败时抛异常 |
| `maxProcessingTimeMs` | `10000` | 最大处理时间 |
| `parallelProcessing` | `false` | 并行处理 |
| `threadPoolSize` | `5` | 并行线程数 |

动态配置：

```xml
<setHeader name="transformConfigId"><simple>${header.transformType}</simple></setHeader>
<to uri="jsontransform:dynamic"/>
```

## JSONPath 与 commonFunctions

路由中可以直接使用 JSONPath 提取请求字段，或通过 `commonFunctions` 调用内置/扩展转换函数。参考 `example/routes/PlatformHttp/v3.0.0/platform-http-route.xml` 和 `example/routes/PlatformHttp/v1.0.0/complex-json-transform-route.xml`。

JSONPath 提取到 Exchange Property：

```xml
<setProperty name="extractedOrderId">
  <jsonpath>$.orderId</jsonpath>
</setProperty>
```

调用转换函数：

```xml
<setProperty name="complexOrderResult">
  <method ref="commonFunctions" method="invokeDtsTransform('transformComplexOrder', ${body})" />
</setProperty>
```

`PlatformHttp/v1.0.0` 的 `/api/demo` 演示 `commonFunctions.transformComplexOrder(...)` 和 `commonFunctions.invokeDtsTransform(...)`。`PlatformHttp/v2.0.0` 的 `/2.0.0/api/demo` 只保留 DTS 通用入口串联演示。`PlatformHttp/v3.0.0` 的 `/api/transform/order`、`/api/transform/order1` 演示 JSONPath 提取、Header/Property 写入和 JSON 响应处理。

注意：

- JSONPath 路径不存在时可能抛异常，演示路由用于说明写法；正式接口建议增加异常分支或 `suppressExceptions`。
- `commonFunctions` 调用适合演示和复用转换能力，复杂场景建议把转换规则和样例输入一起放在服务版本目录。
- `example/routes/**/log4j2.properties` 不需要手工维护，运行时会自动生成。

## 常见误用

- 不要把 `conditionaltransform` 或 `jsontransform` 放在 `<from>`，它们用于 `<to>`。
- 动态模式必须提供 `transformConfigId` Header 或 Exchange Property。
- `failOnError=false` 会保留错误信息并继续流程，需要后续显式判断。

## 验证

- 输入合法 JSON，检查输出字段是否按规则映射。
- 故意传入缺失配置 ID，确认失败分支符合预期。
- 对可选转换设置 `skipOnError=true`，确认主流程不中断。
- 对 `PlatformHttp/v3.0.0` 调用 `/api/transform/order`，检查 JSONPath 提取和响应编码。
- 对 `PlatformHttp/v1.0.0` 调用 `/api/transform/complex-order`，检查 DataSonnet/conditionaltransform 转换链路。
- 对 `PlatformHttp/v1.0.0` 调用 `/api/demo`，检查 `commonFunctions` 与 DTS 通用入口调用。
- 对 `PlatformHttp/v2.0.0` 调用 `/2.0.0/api/demo`，检查 DTS 通用入口串联输出。
