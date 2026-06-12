# 管理 API 响应契约

本交付文档说明 LightESB 管理 API 的标准响应和兼容期要求。

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
| `error` | 失败响应错误摘要或结构化错误 |
| `timestamp` | 服务端毫秒时间戳 |
| `requestId` | 请求追踪标识 |

## 客户端解析

- 前端和 CLI 优先按 `ApiResponse<T>` 契约解析标准响应。
- 旧响应 fallback 只保留一个版本。
- 所有 fallback 代码必须标记 `LIGHTESB_LEGACY_COMPAT`，后续使用 `rg "LIGHTESB_LEGACY_COMPAT"` 清理。

## 后端约束

后端本轮通过 `Map<String,Object>` 响应工厂输出标准字段，保持现有 `ResponseEntity<Map<String,Object>>` Controller 风格，降低旧接口迁移风险。

## 不适用范围

Camel 业务路由异常响应不强行改为管理 API 响应结构。业务路由仍输出业务报文格式，并保留运行时上下文。

