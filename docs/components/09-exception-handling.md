# 异常处理与错误响应

## 用途

LightESB 提供统一异常模型和全局兜底响应。业务路由可以依赖默认兜底，也可以对权限、参数等明确异常做局部 `doTry/doCatch`，返回更清晰的业务错误。

管理 API 和 Camel 业务路由的异常响应不强行统一：

- 管理 API 面向前端、CLI 和控制面调用方，统一使用 `success/data/error/timestamp/requestId`。
- Camel 业务路由面向存量系统协议，继续保留业务报文和 `exchangeId`、`routeId`、`serviceName`、`serviceVersion` 等运行时上下文。
- 两条链路可以共享错误分类和 HTTP 码建议，但不要把管理 API 响应结构直接套到业务路由上。

## 常见映射

| 异常类型 | 建议 HTTP 码 |
| --- | --- |
| 参数错误、JSON 格式错误 | 400 |
| 权限失败 | 403 |
| 资源不存在 | 404 |
| 网络或数据库不可用 | 503 |
| 超时 | 504 |
| 其他未处理异常 | 500 |

## 局部处理样例

```xml
<doTry>
  <!-- 业务处理 -->
  <doCatch>
    <exception>java.lang.IllegalArgumentException</exception>
    <setHeader name="CamelHttpResponseCode"><constant>400</constant></setHeader>
    <setBody><simple>{"error":"INVALID_ARGUMENT","message":"${exception.message}"}</simple></setBody>
    <process ref="jsonResponseProcessor"/>
  </doCatch>
</doTry>
```

## 建议

- 权限和参数校验错误建议在业务路由局部捕获，明确返回 400/403。
- 其他未预期异常交给全局兜底。
- 异常分支也要使用 `servicelog:warn` 或 `servicelog:error` 记录。
- 响应前调用 `jsonResponseProcessor`，保证编码一致。
- 控制面接口的通用异常应由 Spring 全局异常处理返回管理 API 标准失败响应；涉及状态回写或补偿的业务 catch 可以保留。

## 验证

- 人工触发参数错误，返回 400。
- 人工触发权限错误，返回 403。
- 人工抛出未处理异常，确认返回标准错误响应且日志可定位。
