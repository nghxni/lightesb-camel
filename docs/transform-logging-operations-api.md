# Transform 与日志重载 API

本文说明运行时转换规则校验、测试和服务日志配置重载。错误响应使用
[管理 API 响应契约](api-response-contract.md)中的标准信封；成功响应保留
各端点下文列出的字段。

## Transform 规则来源

规则文件只从已加载服务版本目录读取：

```text
lightesb-camel-app/{serviceName}/{serviceVersion}/
```

文件名必须包含 `transform`，后缀为 `.yml`、`.yaml` 或 `.json`。配置 ID 在
当前运行时全局唯一。文件热更新解析或校验失败时，运行时继续使用最后一次有效
配置。

## 重载已跟踪规则

```bash
curl -X POST http://127.0.0.1:8080/api/transform/configs/reload
```

该接口只重载运行时已跟踪的服务版本目录，不扫描全局目录。

成功响应字段示例：

```json
{
  "success": true,
  "message": "配置重新加载成功",
  "total": 2
}
```

任一目录包含无效规则时返回 HTTP `400` 和
`TRANSFORM_CONFIG_RELOAD_FAILED`。

## 校验规则

```bash
curl -X POST http://127.0.0.1:8080/api/transform/configs/validate \
  -H "Content-Type: application/json" \
  -d '{
    "id": "orderTransform",
    "name": "Order Transform",
    "transformations": [{
      "id": "orderId",
      "source": {"path": "$.id"},
      "target": {"path": "$.orderId"},
      "transformType": "DIRECT"
    }]
  }'
```

响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `success` | boolean | 校验调用是否完成。 |
| `valid` | boolean | 规则结构是否有效。 |
| `message` | string | 校验结果摘要。 |
| `errors` | string[] | ID、名称、映射、路径或参数错误。 |

无效规则仍返回 HTTP `200`，调用方必须检查 `valid`。

## 执行真实转换测试

```bash
curl -X POST http://127.0.0.1:8080/api/transform/test \
  -H "Content-Type: application/json" \
  -d '{"configId":"orderTransform","sourceJson":"{\"id\":\"ORD-001\"}"}'
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `configId` | string | 是 | 已加载且启用的规则 ID。 |
| `sourceJson` | string | 是 | 非空 JSON 字符串，不接受对象替代。 |

成功响应字段示例：

```json
{
  "success": true,
  "result": {"orderId": "ORD-001"},
  "processingTime": 4
}
```

该接口执行真实 JSON Transform 处理，不是回显。

| HTTP | 错误码 | 场景 |
| --- | --- | --- |
| `400` | `VALIDATION_ERROR` | 请求字段缺失、为空或类型错误。 |
| `404` | `TRANSFORM_CONFIG_NOT_FOUND` | 规则 ID 未加载。 |
| `400` | `TRANSFORM_TEST_FAILED` | 规则禁用、JSON 非法或转换失败。 |

## 重载服务日志配置

按 route `fileKey`：

```bash
curl -X POST \
  "http://127.0.0.1:8080/api/logging/reload/PlatformHttp@v3.0.0@platform-http-route.xml"
```

按服务版本重载全部已加载 logger：

```bash
curl -X POST \
  "http://127.0.0.1:8080/api/logging/reload/PlatformHttp@v3.0.0"
```

兼容入口：

```bash
curl -X POST \
  "http://127.0.0.1:8080/api/lightesb/config/logging/reconfigure/PlatformHttp/v3.0.0"
```

运行时使用已加载服务的配置定位服务版本目录，重新读取日志配置、重建 logger
并清除对应健康缓存。

| HTTP | 错误码 | 场景 |
| --- | --- | --- |
| `400` | `SERVICE_LOG_CONFIG_NOT_FOUND` | 服务或 fileKey 未加载。 |
| `500` | `INTERNAL_ERROR` | 服务目录消失或底层重配失败。 |

成功只表示 logger 已重建。调用后应发送一条测试请求，并检查目标服务版本目录
下的 `logs/`。
