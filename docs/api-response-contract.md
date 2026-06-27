# 管理 API 响应契约

本交付文档说明 LightESB 管理 API 的标准响应要求。

## 标准响应

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": 1781193600000,
  "requestId": "01HZX..."
}
```

字段：

| 字段 | 说明 |
| --- | --- |
| `success` | 请求是否成功 |
| `data` | 成功响应数据 |
| `error` | 失败响应结构化错误，字段为 `code/message/details` |
| `timestamp` | 服务端毫秒时间戳 |
| `requestId` | 请求追踪标识 |

失败响应示例：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数不能为空",
    "details": null
  },
  "timestamp": 1781193600000,
  "requestId": "01HZX..."
}
```

## 客户端解析

- 前端和 CLI 按 `ApiResponse<T>` 契约解析标准响应。
- 成功响应读取 `data`。
- 失败响应读取 `error.message`，必要时结合 `error.code` 和 `error.details` 排查。
- 非标准管理响应不再作为裸 JSON 兼容处理。

## 后端约束

后端通过 `Map<String,Object>` 响应工厂和管理 API 响应包装器输出标准字段，保持现有 `ResponseEntity<Map<String,Object>>` Controller 风格，降低旧接口迁移风险。

## 不适用范围

Camel 业务路由异常响应不强行改为管理 API 响应结构。业务路由仍输出业务报文格式，并保留运行时上下文。
