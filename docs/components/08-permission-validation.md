# 权限校验

## 用途

`permissionCheckProcessor` 用于在路由中按 IP、CIDR、正则和 Token 组合规则做访问校验。

## 使用方式

```xml
<process ref="permissionCheckProcessor"/>
```

建议捕获权限异常并返回 403：

```xml
<doTry>
  <process ref="permissionCheckProcessor"/>
  <doCatch>
    <exception>com.oureman.soa.lightesb.core.processor.PermissionCheckProcessor$PermissionDeniedException</exception>
    <setHeader name="CamelHttpResponseCode"><constant>403</constant></setHeader>
    <setBody><simple>{"error":"PERMISSION_DENIED","message":"${exception.message}"}</simple></setBody>
  </doCatch>
</doTry>
```

## PERMISSION_TYPE

| 值 | 规则 |
| --- | --- |
| `1` | 精确 IP |
| `2` | CIDR |
| `3` | 正则 |
| `4` | Token |
| `5` | IP + Token |
| `6` | CIDR + Token |
| `7` | 正则 + Token |
| `8` | 全部放行 |

## 输入与输出

输入：

- `client.ip`
- `Token`
- `SenderID`

校验通过后：

- `exchangeProperty.permission.checked=true`
- `exchangeProperty.permission.applicationCode=<applicationCode>`

## 常见问题

- Token 默认从 Exchange 属性 `Token` 读取，不等同于自动读取 `Authorization` 头。
- 未找到规则会拒绝。
- 未知类型会按 warn 处理并默认放行，生产使用前应避免误配。
